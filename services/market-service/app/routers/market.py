from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..core.auth import get_current_user, get_current_teacher
from ..models.market import calculate_price_by_problem_count, calculate_seller_earning
from ..schemas.market import (
    MarketProductCreate, MarketProductUpdate, MarketProductResponse,
    MarketProductListResponse, PurchaseWithPointsRequest, MarketPurchaseResponse,
    MarketReviewCreate, MarketReviewResponse, UserPointResponse,
    PointChargeRequest, PointTransactionResponse, PurchaseWithPointsResponse
)
from ..services.market_service import MarketService
from ..services.point_service import PointService

router = APIRouter(prefix="/market", tags=["market"])


# ==================== 상품 관리 API ====================

@router.get("/products", response_model=List[MarketProductListResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    subject: Optional[str] = Query(None, description="과목 필터 (국어, 수학, 영어, 전체)"),
    search: Optional[str] = Query(None, description="검색어"),
    search_field: str = Query("title", description="검색 필드 (title, tags, author)"),
    sort_by: str = Query("created_at", description="정렬 기준 (created_at, price, satisfaction_rate)"),
    sort_order: str = Query("desc", description="정렬 순서 (asc, desc)"),
    db: Session = Depends(get_db)
):
    """상품 목록 조회 (검색, 필터링, 정렬 지원)"""
    products = await MarketService.get_products(
        db=db,
        skip=skip,
        limit=limit,
        subject_filter=subject,
        search=search,
        search_field=search_field,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return products


@router.get("/products/{product_id}", response_model=MarketProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """상품 상세 조회"""
    product = await MarketService.get_product_detail_with_preview(db, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 조회수 증가 (자기 상품이 아닌 경우에만)
    if product.seller_id != current_user["id"]:
        await MarketService.increment_view_count(db, product_id)

    return product


@router.post("/products", response_model=MarketProductResponse)
async def create_product(
    product_data: MarketProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """상품 등록 (워크시트 복사본 생성)"""
    # 1. 워크시트 소유권 확인
    is_owner = await MarketService.verify_worksheet_ownership(
        current_user["id"],
        product_data.original_worksheet_id,
        product_data.original_service
    )
    if not is_owner:
        raise HTTPException(status_code=403, detail="해당 워크시트의 소유자만 상품을 등록할 수 있습니다.")

    # 2. 중복 상품 확인
    existing = await MarketService.check_duplicate_product(
        db, product_data.original_service, product_data.original_worksheet_id
    )
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 워크시트입니다.")

    # 3. 구매한 워크시트 재등록 방지
    is_purchased = await MarketService.check_purchased_worksheet(
        db, current_user["id"], product_data.original_service, product_data.original_worksheet_id
    )
    if is_purchased:
        raise HTTPException(status_code=400, detail="구매한 워크시트는 다시 등록할 수 없습니다.")

    # 4. 상품 생성
    try:
        product = await MarketService.create_product_from_worksheet(
            db=db,
            product_data=product_data,
            seller_id=current_user["id"],
            seller_name=current_user["name"]
        )
        
        # 5. 신상품 알림 전송 (모든 선생님에게)
        from ..utils.notification_helper import send_market_new_product_notification
        import httpx

        # auth-service에서 모든 선생님 목록 가져오기
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://auth-service:8000/api/auth/teachers/all",
                    timeout=5.0
                )
                if response.status_code == 200:
                    teachers = response.json()
                    # 본인을 제외한 모든 선생님에게 알림 전송
                    for teacher in teachers:
                        if teacher["id"] != current_user["id"]:
                            try:
                                await send_market_new_product_notification(
                                    receiver_id=teacher["id"],
                                    receiver_type="teacher",
                                    seller_id=current_user["id"],
                                    seller_name=current_user["name"],
                                    product_id=product.id,
                                    product_title=product.title,
                                    price=product.price
                                )
                            except Exception as e:
                                print(f"⚠️ 알림 전송 실패 (teacher_id={teacher['id']}): {e}")
        except Exception as e:
            print(f"⚠️ 선생님 목록 조회 실패 (알림 전송 생략): {e}")
        
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-products", response_model=List[MarketProductListResponse])
async def get_my_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """내 상품 목록 조회"""
    products = await MarketService.get_my_products(
        db=db,
        seller_id=current_user["id"],
        skip=skip,
        limit=limit
    )
    return products


@router.patch("/products/{product_id}", response_model=MarketProductResponse)
async def update_product(
    product_id: int,
    update_data: MarketProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """상품 수정 (제목, 설명만 수정 가능)"""
    product = await MarketService.update_product(
        db=db,
        product_id=product_id,
        seller_id=current_user["id"],
        update_data=update_data
    )

    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없거나 수정 권한이 없습니다.")

    return product


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """상품 삭제"""
    success = await MarketService.delete_product(
        db=db,
        product_id=product_id,
        seller_id=current_user["id"]
    )

    if not success:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없거나 삭제 권한이 없습니다.")

    return {"message": "상품이 성공적으로 삭제되었습니다."}


# ==================== 포인트 시스템 API ====================

@router.get("/points/balance", response_model=UserPointResponse)
async def get_point_balance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """내 포인트 잔액 조회"""
    balance = await PointService.get_user_points(db, current_user["id"])
    return balance


@router.post("/points/charge")
async def charge_points(
    charge_data: PointChargeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """포인트 충전"""
    transaction = await PointService.charge_points(
        db=db,
        user_id=current_user["id"],
        amount=charge_data.amount
    )
    return {
        "message": f"{charge_data.amount:,} 포인트가 충전되었습니다.",
        "transaction_id": transaction.id,
        "new_balance": transaction.balance_after
    }


@router.get("/points/transactions", response_model=List[PointTransactionResponse])
async def get_point_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """포인트 거래 내역"""
    transactions = await PointService.get_user_transactions(
        db=db,
        user_id=current_user["id"],
        skip=skip,
        limit=limit
    )
    return transactions


# ==================== 구매 시스템 API ====================

@router.post("/purchase", response_model=PurchaseWithPointsResponse)
async def purchase_with_points(
    purchase_data: PurchaseWithPointsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """포인트로 상품 구매"""
    # 1. 상품 정보 확인
    product = await MarketService.get_product_by_id(db, purchase_data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 2. 자기 상품 구매 방지
    if product.seller_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="자신의 상품은 구매할 수 없습니다.")

    # 3. 중복 구매 확인
    already_purchased = await MarketService.check_already_purchased(
        db, current_user["id"], purchase_data.product_id
    )
    if already_purchased:
        raise HTTPException(status_code=400, detail="이미 구매한 상품입니다.")

    # 4. 포인트로 구매 처리
    try:
        purchase_result = await MarketService.purchase_with_points(
            db=db,
            buyer_id=current_user["id"],
            buyer_name=current_user["name"],
            product_id=purchase_data.product_id
        )
        
        # 5. 판매자에게 판매 알림 전송
        from ..utils.notification_helper import send_market_sale_notification
        try:
            await send_market_sale_notification(
                seller_id=product.seller_id,
                seller_type="teacher",  # 마켓은 선생님만 판매 가능
                buyer_id=current_user["id"],
                buyer_name=current_user["name"],
                product_id=product.id,
                product_title=product.title,
                amount=product.price
            )
        except Exception as e:
            print(f"⚠️ 알림 전송 실패 (주요 로직 계속 진행): {e}")
        
        return purchase_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-purchases", response_model=List[MarketPurchaseResponse])
async def get_my_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """내 구매 목록"""
    purchases = await MarketService.get_user_purchases(
        db=db,
        buyer_id=current_user["id"],
        skip=skip,
        limit=limit
    )
    return purchases


@router.get("/purchased/{purchase_id}/worksheet")
async def get_purchased_worksheet(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """구매한 워크시트 조회 (구매자의 워크시트 서비스에 추가된 것)"""
    worksheet = await MarketService.get_purchased_worksheet_by_purchase_id(
        db=db,
        purchase_id=purchase_id,
        buyer_id=current_user["id"]
    )

    if not worksheet:
        raise HTTPException(status_code=404, detail="구매 기록을 찾을 수 없습니다.")

    return worksheet


# ==================== 리뷰 시스템 API ====================

@router.post("/products/{product_id}/reviews", response_model=MarketReviewResponse)
async def create_review(
    product_id: int,
    review_data: MarketReviewCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """리뷰 작성 (구매자만 가능)"""
    # 구매 여부 확인
    purchased = await MarketService.check_already_purchased(
        db, current_user["id"], product_id
    )
    if not purchased:
        raise HTTPException(status_code=403, detail="구매한 상품만 리뷰를 작성할 수 있습니다.")

    # 중복 리뷰 확인
    existing_review = await MarketService.get_user_review(
        db, current_user["id"], product_id
    )
    if existing_review:
        raise HTTPException(status_code=400, detail="이미 리뷰를 작성했습니다.")

    # 리뷰 생성
    review = await MarketService.create_review(
        db=db,
        product_id=product_id,
        reviewer_id=current_user["id"],
        reviewer_name=current_user["name"],
        rating=review_data.rating
    )

    return review


@router.get("/products/{product_id}/reviews", response_model=List[MarketReviewResponse])
async def get_product_reviews(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """상품 리뷰 목록"""
    reviews = await MarketService.get_product_reviews(
        db=db,
        product_id=product_id,
        skip=skip,
        limit=limit
    )
    return reviews


@router.get("/products/{product_id}/reviews/stats")
async def get_product_review_stats(
    product_id: int,
    db: Session = Depends(get_db)
):
    """상품 리뷰 통계"""
    stats = await MarketService.get_product_review_stats(db, product_id)
    return stats
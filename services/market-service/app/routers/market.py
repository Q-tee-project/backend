from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from decimal import Decimal

from ..core.database import get_db
from ..core.config import settings
from ..core.auth import get_current_user, get_current_teacher
from ..schemas.market import (
    MarketProductCreate, MarketProductUpdate, MarketProductResponse,
    MarketProductListResponse, MarketPurchaseCreate, MarketPurchaseResponse,
    MarketReviewCreate, MarketReviewResponse
)
from ..services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/products", response_model=List[MarketProductListResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    subject: Optional[str] = Query(None, description="과목 필터 (국어, 수학, 영어, 전체)"),
    search: Optional[str] = Query(None, description="검색어"),
    sort_by: str = Query("created_at", description="정렬 기준 (created_at, price, popularity)"),
    sort_order: str = Query("desc", description="정렬 순서 (asc, desc)"),
    db: Session = Depends(get_db)
):
    """상품 목록 조회"""
    products = MarketService.get_products(
        db=db,
        skip=skip,
        limit=limit,
        subject_filter=subject,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return [
        MarketProductListResponse(
            id=product.id,
            title=product.title,
            price=product.price,
            seller_name=product.seller_name,
            subject_type=product.subject_type,
            tags=product.tags,
            main_image=product.main_image,
            view_count=product.view_count,
            purchase_count=product.purchase_count,
            created_at=product.created_at
        )
        for product in products
    ]


@router.get("/products/{product_id}", response_model=MarketProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """상품 상세 조회"""
    product = MarketService.get_product_by_id(db, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    return MarketProductResponse.from_orm(product)


@router.post("/products", response_model=MarketProductResponse)
async def create_product(
    product_data: MarketProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """상품 등록"""
    try:
        product = await MarketService.create_product(
            db=db,
            product_data=product_data,
            seller_id=current_user["id"],
            seller_name=current_user["name"]
        )

        return MarketProductResponse.from_orm(product)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="상품 등록 중 오류가 발생했습니다.")


@router.get("/my-products", response_model=List[MarketProductListResponse])
async def get_my_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """내 상품 목록 조회"""
    products = MarketService.get_my_products(
        db=db,
        seller_id=current_user["id"],
        skip=skip,
        limit=limit
    )

    return [
        MarketProductListResponse(
            id=product.id,
            title=product.title,
            price=product.price,
            seller_name=product.seller_name,
            subject_type=product.subject_type,
            tags=product.tags,
            main_image=product.main_image,
            view_count=product.view_count,
            purchase_count=product.purchase_count,
            created_at=product.created_at
        )
        for product in products
    ]


@router.patch("/products/{product_id}", response_model=MarketProductResponse)
async def update_product(
    product_id: int,
    update_data: MarketProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """상품 수정"""
    product = MarketService.update_product(
        db=db,
        product_id=product_id,
        seller_id=current_user["id"],
        update_data=update_data
    )

    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없거나 수정 권한이 없습니다.")

    return MarketProductResponse.from_orm(product)


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_teacher)
):
    """상품 삭제"""
    success = MarketService.delete_product(
        db=db,
        product_id=product_id,
        seller_id=current_user["id"]
    )

    if not success:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없거나 삭제 권한이 없습니다.")

    return {"message": "상품이 성공적으로 삭제되었습니다."}


@router.post("/purchases", response_model=MarketPurchaseResponse)
async def purchase_product(
    purchase_data: MarketPurchaseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """상품 구매"""
    try:
        purchase = await MarketService.purchase_product(
            db=db,
            purchase_data=purchase_data,
            buyer_id=current_user["id"],
            buyer_name=current_user["name"]
        )

        return MarketPurchaseResponse.from_orm(purchase)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="구매 처리 중 오류가 발생했습니다.")


@router.get("/my-purchases", response_model=List[MarketPurchaseResponse])
async def get_my_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """내 구매 목록"""
    purchases = MarketService.get_user_purchases(
        db=db,
        buyer_id=current_user["id"],
        skip=skip,
        limit=limit
    )

    return [MarketPurchaseResponse.from_orm(purchase) for purchase in purchases]


@router.get("/products/{product_id}/download")
async def download_purchased_worksheet(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """구매한 문제지 다운로드"""
    worksheet_data = await MarketService.get_purchased_worksheet(
        db=db,
        product_id=product_id,
        buyer_id=current_user["id"]
    )

    if not worksheet_data:
        raise HTTPException(status_code=404, detail="구매하지 않은 상품이거나 문제지를 찾을 수 없습니다.")

    return worksheet_data


@router.post("/products/{product_id}/images")
async def upload_product_images(
    product_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """상품 이미지 업로드"""
    # 상품 소유권 확인
    product = MarketService.get_product_by_id(db, product_id)
    if not product or product.seller_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없거나 업로드 권한이 없습니다.")

    if len(files) > 7:
        raise HTTPException(status_code=400, detail="최대 7개의 이미지만 업로드할 수 있습니다.")

    uploaded_files = []
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(product_id))
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"파일 크기는 {settings.MAX_FILE_SIZE}바이트를 초과할 수 없습니다.")

        # 파일 확장자 확인
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

        # 고유한 파일명 생성
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        # 파일 저장
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        uploaded_files.append(unique_filename)

    # 데이터베이스에 이미지 정보 업데이트
    current_images = product.images or []
    updated_images = current_images + uploaded_files

    # 첫 번째 이미지를 메인 이미지로 설정
    if not product.main_image and uploaded_files:
        product.main_image = uploaded_files[0]

    product.images = updated_images
    db.commit()

    return {
        "message": f"{len(uploaded_files)}개의 이미지가 성공적으로 업로드되었습니다.",
        "uploaded_files": uploaded_files
    }
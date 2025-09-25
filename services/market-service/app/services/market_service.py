from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.market import (
    MarketProduct, MarketPurchase, MarketReview, ReviewRating,
    calculate_price_by_problem_count, calculate_seller_earning,
    generate_tags_from_metadata, calculate_satisfaction_rate
)
from ..schemas.market import (
    MarketProductCreate, MarketProductUpdate, MarketProductResponse,
    MarketProductListResponse, PurchaseWithPointsResponse, MarketPurchaseResponse,
    MarketReviewResponse
)
from ..services.point_service import PointService
from .external_service import ExternalService


class MarketService:
    """마켓플레이스 비즈니스 로직"""

    # ==================== 상품 관리 ====================

    @staticmethod
    async def verify_worksheet_ownership(
        user_id: int, worksheet_id: int, service: str
    ) -> bool:
        """워크시트 소유권 확인"""
        return await ExternalService.check_worksheet_ownership(
            service, worksheet_id, user_id
        )

    @staticmethod
    async def check_duplicate_product(
        db: Session, service: str, worksheet_id: int
    ) -> Optional[MarketProduct]:
        """중복 상품 확인"""
        return db.query(MarketProduct).filter(
            MarketProduct.original_service == service,
            MarketProduct.original_worksheet_id == worksheet_id
        ).first()

    @staticmethod
    async def create_product_from_worksheet(
        db: Session,
        product_data: MarketProductCreate,
        seller_id: int,
        seller_name: str
    ) -> MarketProductResponse:
        """워크시트로부터 상품 생성"""

        # 1. 원본 워크시트 정보 가져오기
        worksheet_info = await ExternalService.get_worksheet_details(
            product_data.original_service,
            product_data.original_worksheet_id
        )

        if not worksheet_info:
            raise ValueError("원본 워크시트를 찾을 수 없습니다.")

        # 2. 문제 수에 따른 가격 자동 계산
        problem_count = len(worksheet_info.get('problems', []))
        price = calculate_price_by_problem_count(problem_count)

        # 3. 태그 자동 생성
        tags = generate_tags_from_metadata(
            worksheet_info.get('school_level', ''),
            worksheet_info.get('grade', 1),
            worksheet_info.get('subject_type', ''),
            worksheet_info.get('semester'),
            worksheet_info.get('unit_info')
        )

        # 4. 미리보기 문제 검증 제거됨 - 프론트엔드에서 이미지 생성
        worksheet_problems = worksheet_info.get('problems', [])

        # 5. 상품 생성
        db_product = MarketProduct(
            title=product_data.title,
            description=product_data.description,
            price=price,
            seller_id=seller_id,
            seller_name=seller_name,

            # 워크시트 복사본 데이터
            worksheet_title=worksheet_info.get('title', ''),
            worksheet_problems=worksheet_problems,
            problem_count=problem_count,

            # 메타데이터
            school_level=worksheet_info.get('school_level', ''),
            grade=worksheet_info.get('grade', 1),
            subject_type=worksheet_info.get('subject_type', ''),
            semester=worksheet_info.get('semester'),
            unit_info=worksheet_info.get('unit_info'),
            tags=tags,

            # 미리보기 설정 제거됨

            # 원본 참조
            original_service=product_data.original_service,
            original_worksheet_id=product_data.original_worksheet_id
        )

        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        # 6. 응답 데이터 구성 - 미리보기 제거됨

        return MarketProductResponse(
            id=db_product.id,
            title=db_product.title,
            description=db_product.description,
            price=db_product.price,
            seller_id=db_product.seller_id,
            seller_name=db_product.seller_name,
            worksheet_title=db_product.worksheet_title,
            problem_count=db_product.problem_count,
            school_level=db_product.school_level,
            grade=db_product.grade,
            subject_type=db_product.subject_type,
            semester=db_product.semester,
            unit_info=db_product.unit_info,
            tags=db_product.tags,
            # 미리보기 데이터 제거됨
            original_service=db_product.original_service,
            original_worksheet_id=db_product.original_worksheet_id,
            view_count=db_product.view_count,
            purchase_count=db_product.purchase_count,
            total_reviews=db_product.total_reviews,
            satisfaction_rate=db_product.satisfaction_rate,
            created_at=db_product.created_at,
            updated_at=db_product.updated_at
        )

    @staticmethod
    async def get_products(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        subject_filter: Optional[str] = None,
        search: Optional[str] = None,
        search_field: str = "title",
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[MarketProductListResponse]:
        """상품 목록 조회 (검색, 필터링, 정렬)"""

        query = db.query(MarketProduct)

        # 과목 필터
        if subject_filter and subject_filter != "전체":
            query = query.filter(MarketProduct.subject_type == subject_filter)

        # 검색
        if search:
            search_term = f"%{search.lower()}%"
            if search_field == "title":
                query = query.filter(MarketProduct.title.ilike(search_term))
            elif search_field == "tags":
                # JSON 배열에서 검색 (PostgreSQL 기준)
                query = query.filter(
                    MarketProduct.tags.cast(db.String).ilike(search_term)
                )
            elif search_field == "author":
                query = query.filter(MarketProduct.seller_name.ilike(search_term))

        # 정렬
        order_func = desc if sort_order == "desc" else asc
        if sort_by == "price":
            query = query.order_by(order_func(MarketProduct.price))
        elif sort_by == "satisfaction_rate":
            query = query.order_by(desc(MarketProduct.satisfaction_rate))
        else:  # created_at
            query = query.order_by(desc(MarketProduct.created_at))

        products = query.offset(skip).limit(limit).all()

        # 응답 변환 - 미리보기 제거됨
        result = []
        for product in products:
            # 대표 미리보기 문제 가져오기 - 제거됨, 프론트엔드에서 이미지 생성

            result.append(MarketProductListResponse(
                id=product.id,
                title=product.title,
                price=product.price,
                seller_name=product.seller_name,
                subject_type=product.subject_type,
                tags=product.tags or [],
                problem_count=product.problem_count,
                school_level=product.school_level,
                grade=product.grade,
                # main_preview_problem 제거됨 - 프론트에서 이미지 생성
                satisfaction_rate=product.satisfaction_rate,
                view_count=product.view_count,
                purchase_count=product.purchase_count,
                created_at=product.created_at
            ))

        return result

    @staticmethod
    async def get_product_detail_with_preview(
        db: Session, product_id: int
    ) -> Optional[MarketProductResponse]:
        """미리보기 문제와 함께 상품 상세 정보 조회"""

        product = db.query(MarketProduct).filter(MarketProduct.id == product_id).first()
        if not product:
            return None

        # 미리보기 문제 구성
        preview_problem_details = []
        if product.preview_problems and product.worksheet_problems:
            preview_problem_details = [
                PreviewProblem(
                    id=p.get('id'),
                    sequence_order=p.get('sequence_order', 0),
                    question=p.get('question', ''),
                    problem_type=p.get('problem_type', ''),
                    choices=p.get('choices'),
                    difficulty=p.get('difficulty', '')
                )
                for p in product.worksheet_problems
                if p.get('id') in product.preview_problems
            ]

        return MarketProductResponse(
            id=product.id,
            title=product.title,
            description=product.description,
            price=product.price,
            seller_id=product.seller_id,
            seller_name=product.seller_name,
            worksheet_title=product.worksheet_title,
            problem_count=product.problem_count,
            school_level=product.school_level,
            grade=product.grade,
            subject_type=product.subject_type,
            semester=product.semester,
            unit_info=product.unit_info,
            tags=product.tags or [],
            preview_problems=preview_problem_details,
            main_preview_problem_id=product.main_preview_problem_id,
            original_service=product.original_service,
            original_worksheet_id=product.original_worksheet_id,
            view_count=product.view_count,
            purchase_count=product.purchase_count,
            total_reviews=product.total_reviews,
            satisfaction_rate=product.satisfaction_rate,
            created_at=product.created_at,
            updated_at=product.updated_at
        )

    @staticmethod
    async def increment_view_count(db: Session, product_id: int):
        """조회수 증가"""
        product = db.query(MarketProduct).filter(MarketProduct.id == product_id).first()
        if product:
            product.view_count += 1
            db.commit()

    @staticmethod
    async def get_product_by_id(db: Session, product_id: int) -> Optional[MarketProduct]:
        """상품 기본 정보 조회"""
        return db.query(MarketProduct).filter(MarketProduct.id == product_id).first()

    @staticmethod
    async def get_my_products(
        db: Session,
        seller_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[MarketProductListResponse]:
        """내 상품 목록"""
        products = (
            db.query(MarketProduct)
            .filter(MarketProduct.seller_id == seller_id)
            .order_by(desc(MarketProduct.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        # 응답 변환 - 미리보기 제거됨
        result = []
        for product in products:
            # 미리보기 로직 제거됨 - 프론트엔드에서 이미지 생성

            result.append(MarketProductListResponse(
                id=product.id,
                title=product.title,
                price=product.price,
                seller_name=product.seller_name,
                subject_type=product.subject_type,
                tags=product.tags or [],
                problem_count=product.problem_count,
                school_level=product.school_level,
                grade=product.grade,
                # main_preview_problem 제거됨
                satisfaction_rate=product.satisfaction_rate,
                view_count=product.view_count,
                purchase_count=product.purchase_count,
                created_at=product.created_at
            ))

        return result

    @staticmethod
    async def update_product(
        db: Session,
        product_id: int,
        seller_id: int,
        update_data: MarketProductUpdate
    ) -> Optional[MarketProductResponse]:
        """상품 수정 (제목, 설명만 수정 가능)"""

        product = db.query(MarketProduct).filter(
            MarketProduct.id == product_id,
            MarketProduct.seller_id == seller_id
        ).first()

        if not product:
            return None

        # 허용된 필드만 업데이트 - 미리보기 제거됨
        if update_data.title is not None:
            product.title = update_data.title
        if update_data.description is not None:
            product.description = update_data.description
        # 미리보기 관련 업데이트 제거됨

        db.commit()

        # 업데이트된 정보 반환
        return await MarketService.get_product_detail_with_preview(db, product_id)

    @staticmethod
    async def delete_product(db: Session, product_id: int, seller_id: int) -> bool:
        """상품 삭제 (하드 삭제)"""
        product = db.query(MarketProduct).filter(
            MarketProduct.id == product_id,
            MarketProduct.seller_id == seller_id
        ).first()

        if not product:
            return False

        # 구매 기록이 있으면 삭제 불가
        purchase_count = db.query(MarketPurchase).filter(
            MarketPurchase.product_id == product_id
        ).count()

        if purchase_count > 0:
            raise ValueError("구매 기록이 있는 상품은 삭제할 수 없습니다.")

        db.delete(product)
        db.commit()
        return True

    # ==================== 구매 시스템 ====================

    @staticmethod
    async def check_already_purchased(
        db: Session, buyer_id: int, product_id: int
    ) -> bool:
        """구매 여부 확인"""
        purchase = db.query(MarketPurchase).filter(
            MarketPurchase.buyer_id == buyer_id,
            MarketPurchase.product_id == product_id
        ).first()
        return purchase is not None

    @staticmethod
    async def purchase_with_points(
        db: Session,
        buyer_id: int,
        buyer_name: str,
        product_id: int
    ) -> PurchaseWithPointsResponse:
        """포인트로 상품 구매 및 워크시트 복사"""

        # 상품 정보 가져오기
        product = db.query(MarketProduct).filter(MarketProduct.id == product_id).first()
        if not product:
            raise ValueError("상품을 찾을 수 없습니다.")

        price = product.price
        seller_earning, platform_fee = calculate_seller_earning(price)

        # 1. 구매자 포인트 차감
        await PointService.spend_points(
            db=db,
            user_id=buyer_id,
            amount=price,
            product_id=product_id,
            description=f"{product.title} 구매"
        )

        # 2. 판매자 포인트 적립
        await PointService.earn_points(
            db=db,
            user_id=product.seller_id,
            amount=seller_earning,
            product_id=product_id,
            description=f"{product.title} 판매 수익"
        )

        # 3. 구매 기록 생성
        purchase = MarketPurchase(
            product_id=product_id,
            buyer_id=buyer_id,
            buyer_name=buyer_name,
            purchase_price=price,
            payment_method="points",
            payment_status="completed"
        )
        db.add(purchase)

        # 4. 상품 통계 업데이트
        product.purchase_count += 1

        db.commit()
        db.refresh(purchase)

        # 5. 구매자의 워크시트 서비스에 복사
        copied_worksheet_id = await ExternalService.copy_worksheet_to_user(
            service=product.original_service,
            worksheet_id=product.original_worksheet_id,
            target_user_id=buyer_id,
            new_title=f"[구매] {product.worksheet_title}"
        )

        if not copied_worksheet_id:
            # 워크시트 복사 실패 시 롤백 처리 (포인트 복구 등)
            # 실제로는 트랜잭션을 사용해야 함
            raise ValueError("워크시트 복사 중 오류가 발생했습니다.")

        # 구매 완료 알림
        await ExternalService.notify_purchase(
            service=product.original_service,
            worksheet_id=product.original_worksheet_id,
            seller_id=product.seller_id,
            buyer_id=buyer_id,
            purchase_id=purchase.id
        )

        # 6. 구매자 포인트 잔액 조회
        remaining_points = await PointService.get_balance(db, buyer_id)

        return PurchaseWithPointsResponse(
            purchase_id=purchase.id,
            product_id=product_id,
            points_spent=price,
            remaining_points=remaining_points,
            seller_earned=seller_earning,
            platform_fee=platform_fee
        )

    @staticmethod
    async def get_user_purchases(
        db: Session,
        buyer_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[MarketPurchaseResponse]:
        """사용자 구매 목록"""
        purchases = (
            db.query(MarketPurchase)
            .join(MarketProduct)
            .filter(MarketPurchase.buyer_id == buyer_id)
            .order_by(desc(MarketPurchase.purchased_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        result = []
        for purchase in purchases:
            result.append(MarketPurchaseResponse(
                id=purchase.id,
                product_id=purchase.product_id,
                product_title=purchase.product.title,
                seller_name=purchase.product.seller_name,
                buyer_id=purchase.buyer_id,
                buyer_name=purchase.buyer_name,
                purchase_price=purchase.purchase_price,
                payment_method=purchase.payment_method,
                payment_status=purchase.payment_status,
                subject_type=purchase.product.subject_type,
                tags=purchase.product.tags or [],
                purchased_at=purchase.purchased_at
            ))

        return result

    # ==================== 리뷰 시스템 ====================

    @staticmethod
    async def get_user_review(
        db: Session, user_id: int, product_id: int
    ) -> Optional[MarketReview]:
        """사용자의 특정 상품 리뷰 조회"""
        return db.query(MarketReview).filter(
            MarketReview.reviewer_id == user_id,
            MarketReview.product_id == product_id
        ).first()

    @staticmethod
    async def create_review(
        db: Session,
        product_id: int,
        reviewer_id: int,
        reviewer_name: str,
        rating: str
    ) -> MarketReviewResponse:
        """리뷰 작성 및 상품 통계 업데이트"""

        # 리뷰 생성
        review = MarketReview(
            product_id=product_id,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            rating=rating
        )
        db.add(review)

        # 상품 리뷰 통계 업데이트
        product = db.query(MarketProduct).filter(MarketProduct.id == product_id).first()
        if product:
            product.total_reviews += 1

            if rating == ReviewRating.RECOMMEND:
                product.recommend_count += 1
            elif rating == ReviewRating.NORMAL:
                product.normal_count += 1
            elif rating == ReviewRating.NOT_RECOMMEND:
                product.not_recommend_count += 1

            # 만족도 재계산
            product.satisfaction_rate = calculate_satisfaction_rate(
                product.recommend_count, product.total_reviews
            )

        db.commit()
        db.refresh(review)

        return MarketReviewResponse.from_orm(review)

    @staticmethod
    async def get_product_reviews(
        db: Session,
        product_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[MarketReviewResponse]:
        """상품 리뷰 목록"""
        reviews = (
            db.query(MarketReview)
            .filter(MarketReview.product_id == product_id)
            .order_by(desc(MarketReview.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [MarketReviewResponse.from_orm(review) for review in reviews]

    @staticmethod
    async def get_product_review_stats(db: Session, product_id: int) -> Dict[str, Any]:
        """상품 리뷰 통계"""
        product = db.query(MarketProduct).filter(MarketProduct.id == product_id).first()
        if not product:
            return {}

        return {
            "satisfaction_rate": product.satisfaction_rate,
            "total_reviews": product.total_reviews,
            "breakdown": {
                "recommend": {
                    "count": product.recommend_count,
                    "percentage": round((product.recommend_count / max(product.total_reviews, 1)) * 100, 1)
                },
                "normal": {
                    "count": product.normal_count,
                    "percentage": round((product.normal_count / max(product.total_reviews, 1)) * 100, 1)
                },
                "not-recommend": {
                    "count": product.not_recommend_count,
                    "percentage": round((product.not_recommend_count / max(product.total_reviews, 1)) * 100, 1)
                }
            }
        }

    # ==================== 기타 ====================

    @staticmethod
    async def get_purchased_worksheet_by_purchase_id(
        db: Session, purchase_id: int, buyer_id: int
    ) -> Optional[Dict[str, Any]]:
        """구매 ID로 구매한 워크시트 정보 조회"""
        purchase = db.query(MarketPurchase).filter(
            MarketPurchase.id == purchase_id,
            MarketPurchase.buyer_id == buyer_id
        ).first()

        if not purchase:
            return None

        # 구매자의 해당 서비스에서 워크시트 접근 권한 확인
        has_access = await ExternalService.check_user_access(
            service=purchase.product.original_service,
            user_id=buyer_id,
            worksheet_id=purchase.product.original_worksheet_id
        )

        if has_access:
            # 구매한 워크시트 정보 반환
            return {
                "purchase_id": purchase.id,
                "product_id": purchase.product_id,
                "title": purchase.product.title,
                "worksheet_title": purchase.product.worksheet_title,
                "service": purchase.product.original_service,
                "original_worksheet_id": purchase.product.original_worksheet_id,
                "purchased_at": purchase.purchased_at,
                "access_granted": True
            }

        return None
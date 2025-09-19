from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..models.market import MarketProduct, MarketPurchase, MarketReview, ProductStatus
from ..schemas.market import (
    MarketProductCreate, MarketProductUpdate, MarketProductResponse,
    MarketPurchaseCreate, MarketReviewCreate
)
from .external_service import ExternalService


class MarketService:
    """마켓 서비스 비즈니스 로직"""

    @staticmethod
    async def create_product(
        db: Session,
        product_data: MarketProductCreate,
        seller_id: int,
        seller_name: str
    ) -> Optional[MarketProduct]:
        """상품 등록"""

        # 원본 문제지 존재 여부 확인
        worksheet_info = await ExternalService.get_worksheet_info(
            product_data.original_service,
            product_data.original_worksheet_id
        )

        if not worksheet_info:
            raise ValueError("원본 문제지를 찾을 수 없습니다.")

        # 문제지 소유권 확인
        is_owner = await ExternalService.check_worksheet_ownership(
            product_data.original_service,
            product_data.original_worksheet_id,
            seller_id
        )

        if not is_owner:
            raise ValueError("해당 문제지에 대한 권한이 없습니다.")

        # 이미 등록된 상품인지 확인
        existing_product = db.query(MarketProduct).filter(
            MarketProduct.original_service == product_data.original_service,
            MarketProduct.original_worksheet_id == product_data.original_worksheet_id,
            MarketProduct.seller_id == seller_id,
            MarketProduct.status != ProductStatus.DELETED
        ).first()

        if existing_product:
            raise ValueError("이미 등록된 문제지입니다.")

        # 새 상품 생성
        db_product = MarketProduct(
            title=product_data.title,
            description=product_data.description,
            price=product_data.price,
            seller_id=seller_id,
            seller_name=seller_name,
            subject_type=product_data.subject_type,
            tags=product_data.tags,
            original_service=product_data.original_service,
            original_worksheet_id=product_data.original_worksheet_id,
            status=ProductStatus.ACTIVE
        )

        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        return db_product

    @staticmethod
    def get_products(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        subject_filter: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[MarketProduct]:
        """상품 목록 조회"""

        query = db.query(MarketProduct).filter(
            MarketProduct.status == ProductStatus.ACTIVE
        )

        # 과목 필터
        if subject_filter and subject_filter != "전체":
            query = query.filter(MarketProduct.subject_type == subject_filter)

        # 검색
        if search:
            query = query.filter(
                MarketProduct.title.ilike(f"%{search}%")
            )

        # 정렬
        order_func = desc if sort_order == "desc" else asc
        if sort_by == "price":
            query = query.order_by(order_func(MarketProduct.price))
        elif sort_by == "popularity":
            query = query.order_by(desc(MarketProduct.purchase_count))
        else:  # created_at
            query = query.order_by(desc(MarketProduct.created_at))

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Optional[MarketProduct]:
        """상품 상세 조회"""
        product = db.query(MarketProduct).filter(
            MarketProduct.id == product_id,
            MarketProduct.status != ProductStatus.DELETED
        ).first()

        if product:
            # 조회수 증가
            product.view_count += 1
            db.commit()

        return product

    @staticmethod
    def get_my_products(
        db: Session,
        seller_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[MarketProduct]:
        """내 상품 목록 조회"""
        return db.query(MarketProduct).filter(
            MarketProduct.seller_id == seller_id,
            MarketProduct.status != ProductStatus.DELETED
        ).order_by(desc(MarketProduct.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def update_product(
        db: Session,
        product_id: int,
        seller_id: int,
        update_data: MarketProductUpdate
    ) -> Optional[MarketProduct]:
        """상품 수정"""
        product = db.query(MarketProduct).filter(
            MarketProduct.id == product_id,
            MarketProduct.seller_id == seller_id,
            MarketProduct.status != ProductStatus.DELETED
        ).first()

        if not product:
            return None

        # 업데이트할 필드만 수정
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)

        return product

    @staticmethod
    def delete_product(db: Session, product_id: int, seller_id: int) -> bool:
        """상품 삭제"""
        product = db.query(MarketProduct).filter(
            MarketProduct.id == product_id,
            MarketProduct.seller_id == seller_id,
            MarketProduct.status != ProductStatus.DELETED
        ).first()

        if not product:
            return False

        product.status = ProductStatus.DELETED
        db.commit()

        return True

    @staticmethod
    async def purchase_product(
        db: Session,
        purchase_data: MarketPurchaseCreate,
        buyer_id: int,
        buyer_name: str
    ) -> Optional[MarketPurchase]:
        """상품 구매"""
        product = db.query(MarketProduct).filter(
            MarketProduct.id == purchase_data.product_id,
            MarketProduct.status == ProductStatus.ACTIVE
        ).first()

        if not product:
            raise ValueError("상품을 찾을 수 없습니다.")

        if product.seller_id == buyer_id:
            raise ValueError("자신의 상품은 구매할 수 없습니다.")

        # 이미 구매한 상품인지 확인
        existing_purchase = db.query(MarketPurchase).filter(
            MarketPurchase.product_id == purchase_data.product_id,
            MarketPurchase.buyer_id == buyer_id
        ).first()

        if existing_purchase:
            raise ValueError("이미 구매한 상품입니다.")

        # 구매 기록 생성
        db_purchase = MarketPurchase(
            product_id=purchase_data.product_id,
            buyer_id=buyer_id,
            buyer_name=buyer_name,
            purchase_price=product.price,
            payment_method=purchase_data.payment_method,
            payment_status="completed"
        )

        db.add(db_purchase)

        # 상품 구매 횟수 증가
        product.purchase_count += 1

        db.commit()
        db.refresh(db_purchase)

        return db_purchase

    @staticmethod
    def get_user_purchases(
        db: Session,
        buyer_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[MarketPurchase]:
        """사용자 구매 목록"""
        return db.query(MarketPurchase).filter(
            MarketPurchase.buyer_id == buyer_id
        ).order_by(desc(MarketPurchase.purchased_at)).offset(skip).limit(limit).all()

    @staticmethod
    def has_purchased(db: Session, product_id: int, buyer_id: int) -> bool:
        """구매 여부 확인"""
        purchase = db.query(MarketPurchase).filter(
            MarketPurchase.product_id == product_id,
            MarketPurchase.buyer_id == buyer_id
        ).first()

        return purchase is not None

    @staticmethod
    async def get_purchased_worksheet(
        db: Session,
        product_id: int,
        buyer_id: int
    ) -> Optional[Dict[Any, Any]]:
        """구매한 문제지 상세 내용 조회"""

        # 구매 확인
        if not MarketService.has_purchased(db, product_id, buyer_id):
            return None

        product = MarketService.get_product_by_id(db, product_id)
        if not product:
            return None

        # 원본 서비스에서 문제지 상세 정보 가져오기
        worksheet_details = await ExternalService.get_worksheet_details(
            product.original_service,
            product.original_worksheet_id
        )

        if worksheet_details:
            # 마켓 상품 정보와 함께 반환
            worksheet_details['market_info'] = {
                'product_id': product.id,
                'title': product.title,
                'price': float(product.price),
                'seller_name': product.seller_name
            }

        return worksheet_details
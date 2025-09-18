from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import enum
from ..core.database import Base


class SubjectType(str, enum.Enum):
    KOREAN = "국어"
    MATH = "수학"
    ENGLISH = "영어"


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"      # 판매중
    INACTIVE = "inactive"  # 판매중지
    SOLD_OUT = "sold_out"  # 품절
    DELETED = "deleted"    # 삭제됨


class MarketProduct(Base):
    """마켓 상품 모델"""
    __tablename__ = "market_products"
    __table_args__ = {"schema": "market_service"}

    id = Column(Integer, primary_key=True, index=True)

    # 기본 정보
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)  # 최대 99,999,999.99원

    # 판매자 정보
    seller_id = Column(Integer, nullable=False, index=True)  # auth-service의 user_id
    seller_name = Column(String(100), nullable=False)

    # 카테고리 및 태그
    subject_type = Column(String(20), nullable=False, index=True)  # 과목
    tags = Column(JSON, nullable=True)  # ["중학교", "1학년", "기출문제"]

    # 원본 문제지 정보
    original_service = Column(String(20), nullable=False)  # "korean", "math", "english"
    original_worksheet_id = Column(Integer, nullable=False)  # 원본 서비스의 worksheet ID

    # 상품 상태
    status = Column(String(20), default=ProductStatus.ACTIVE, nullable=False)

    # 판매 통계
    view_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)

    # 이미지
    images = Column(JSON, nullable=True)  # ["image1.jpg", "image2.jpg"]
    main_image = Column(String(255), nullable=True)

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    purchases = relationship("MarketPurchase", back_populates="product")
    reviews = relationship("MarketReview", back_populates="product")


class MarketPurchase(Base):
    """마켓 구매 기록"""
    __tablename__ = "market_purchases"
    __table_args__ = {"schema": "market_service"}

    id = Column(Integer, primary_key=True, index=True)

    # 구매 정보
    product_id = Column(Integer, ForeignKey("market_service.market_products.id"), nullable=False)
    buyer_id = Column(Integer, nullable=False, index=True)  # auth-service의 user_id
    buyer_name = Column(String(100), nullable=False)

    # 결제 정보
    purchase_price = Column(Numeric(10, 2), nullable=False)  # 구매 당시 가격
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(20), default="completed")

    # 시간 관리
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계
    product = relationship("MarketProduct", back_populates="purchases")


class MarketReview(Base):
    """마켓 리뷰"""
    __tablename__ = "market_reviews"
    __table_args__ = {"schema": "market_service"}

    id = Column(Integer, primary_key=True, index=True)

    # 리뷰 정보
    product_id = Column(Integer, ForeignKey("market_service.market_products.id"), nullable=False)
    reviewer_id = Column(Integer, nullable=False, index=True)  # auth-service의 user_id
    reviewer_name = Column(String(100), nullable=False)

    # 리뷰 내용
    rating = Column(Integer, nullable=False)  # 1-5 별점
    comment = Column(Text, nullable=True)

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    product = relationship("MarketProduct", back_populates="reviews")
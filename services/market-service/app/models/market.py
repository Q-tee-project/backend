from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Numeric, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base


class SubjectType(str, enum.Enum):
    KOREAN = "국어"
    MATH = "수학"
    ENGLISH = "영어"


class ReviewRating(str, enum.Enum):
    RECOMMEND = "recommend"
    NORMAL = "normal"
    NOT_RECOMMEND = "not-recommend"


class MarketProduct(Base):
    """마켓 상품 모델"""
    __tablename__ = "market_products"
    __table_args__ = (
        UniqueConstraint('original_service', 'original_worksheet_id', name='unique_worksheet_product'),
        {"schema": "market_service"}
    )

    id = Column(Integer, primary_key=True, index=True)

    # 상품 기본 정보
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)

    # 판매자 정보
    seller_id = Column(Integer, nullable=False, index=True)
    seller_name = Column(String(100), nullable=False)

    # 워크시트 데이터
    worksheet_title = Column(String(200), nullable=False)
    worksheet_problems = Column(JSON, nullable=False)
    problem_count = Column(Integer, nullable=False)

    # 메타데이터
    school_level = Column(String(20), nullable=False)
    grade = Column(Integer, nullable=False)
    subject_type = Column(String(20), nullable=False, index=True)
    semester = Column(String(10), nullable=True)
    unit_info = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=False)

    # 원본 참조
    original_service = Column(String(20), nullable=False)
    original_worksheet_id = Column(Integer, nullable=False)

    # 통계
    view_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    total_revenue = Column(Integer, default=0)

    # 리뷰 통계
    total_reviews = Column(Integer, default=0)
    recommend_count = Column(Integer, default=0)
    normal_count = Column(Integer, default=0)
    not_recommend_count = Column(Integer, default=0)
    satisfaction_rate = Column(Float, default=0.0)

    # 시간
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
    buyer_id = Column(Integer, nullable=False, index=True)
    buyer_name = Column(String(100), nullable=False)

    # 결제 정보
    purchase_price = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(20), default="completed")

    # 복사된 워크시트 정보
    copied_worksheet_id = Column(Integer, nullable=True)

    # 시간
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
    reviewer_id = Column(Integer, nullable=False, index=True)
    reviewer_name = Column(String(100), nullable=False)

    # 리뷰 내용
    rating = Column(String(20), nullable=False)

    # 시간
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    product = relationship("MarketProduct", back_populates="reviews")


def calculate_price_by_problem_count(problem_count: int) -> int:
    """문제 수에 따른 가격 계산"""
    if problem_count == 10:
        return 1500
    elif problem_count == 20:
        return 3000
    else:
        raise ValueError(f"지원하지 않는 문제 수입니다: {problem_count}")


def calculate_satisfaction_rate(recommend: int, total: int) -> float:
    """만족도 계산 (추천 비율)"""
    if total == 0:
        return 0.0
    return round((recommend / total) * 100, 1)


def generate_tags_from_metadata(school_level: str, grade: int, subject: str,
                               semester: str = None, unit_info: str = None) -> list:
    """워크시트 메타데이터로부터 태그 자동 생성"""
    tags = [school_level, f"{grade}학년", subject]

    if semester:
        tags.append(semester)
    if unit_info:
        tags.append(unit_info)

    return tags

class PointTransactionType(str, enum.Enum):
    CHARGE = "charge"           # 포인트 충전
    PURCHASE = "purchase"       # 상품 구매 (차감)
    EARN = "earn"              # 판매 수익 (적립)
    ADMIN_ADJUST = "admin_adjust"  # 관리자 조정


class UserPoint(Base):
    """사용자 포인트 관리"""
    __tablename__ = "user_points"
    __table_args__ = {"schema": "market_service"}

    user_id = Column(Integer, primary_key=True, index=True)

    # 포인트 잔액
    available_points = Column(Integer, default=0)

    # 통계
    total_earned = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)
    total_charged = Column(Integer, default=0)

    # 시간
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PointTransaction(Base):
    """포인트 거래 내역"""
    __tablename__ = "point_transactions"
    __table_args__ = {"schema": "market_service"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # 거래 정보
    transaction_type = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    # 연관 정보
    product_id = Column(Integer, nullable=True)
    description = Column(String(200), nullable=False)

    # 시간
    created_at = Column(DateTime(timezone=True), server_default=func.now())


PLATFORM_FEE_RATE = 0.1

def calculate_seller_earning(sale_amount: int) -> tuple:
    """판매 수익 계산"""
    platform_fee = int(sale_amount * PLATFORM_FEE_RATE)
    seller_earning = sale_amount - platform_fee
    return seller_earning, platform_fee
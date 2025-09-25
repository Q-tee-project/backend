from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Numeric, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base


class SubjectType(str, enum.Enum):
    KOREAN = "국어"
    MATH = "수학"
    ENGLISH = "영어"


# ProductStatus enum 제거 - 단순 CRUD만 필요


class ReviewRating(str, enum.Enum):
    RECOMMEND = "recommend"        # 추천
    NORMAL = "normal"             # 보통
    NOT_RECOMMEND = "not-recommend" # 추천안함


class MarketProduct(Base):
    """마켓 상품 모델 - Worksheet 복사본 기반"""
    __tablename__ = "market_products"
    __table_args__ = (
        UniqueConstraint('original_service', 'original_worksheet_id', name='unique_worksheet_product'),
        {"schema": "market_service"}
    )

    id = Column(Integer, primary_key=True, index=True)

    # 상품 기본 정보 (수정 가능)
    title = Column(String(200), nullable=False, index=True)  # 상품명 (수정 가능)
    description = Column(Text, nullable=True)  # 상품 설명 (수정 가능)

    # 가격 (자동 계산 - 10문제: 1500원, 20문제: 3000원)
    price = Column(Integer, nullable=False)  # 1500 or 3000

    # 판매자 정보
    seller_id = Column(Integer, nullable=False, index=True)
    seller_name = Column(String(100), nullable=False)

    # 원본 Worksheet 복사본 데이터 (등록 시점 스냅샷)
    worksheet_title = Column(String(200), nullable=False)  # 원본 제목
    worksheet_problems = Column(JSON, nullable=False)      # 전체 문제 복사본
    problem_count = Column(Integer, nullable=False)        # 10 or 20

    # Worksheet 메타데이터 (태그로 사용 - 고정)
    school_level = Column(String(20), nullable=False)      # "중학교", "고등학교"
    grade = Column(Integer, nullable=False)                # 1, 2, 3
    subject_type = Column(String(20), nullable=False, index=True)  # "국어", "수학", "영어"
    semester = Column(String(10), nullable=True)           # "1학기", "2학기"
    unit_info = Column(String(100), nullable=True)         # "1단원", "2단원" 등
    tags = Column(JSON, nullable=False)  # ["중학교", "1학년", "국어", "1학기"] - 자동생성, 고정

    # 미리보기 문제 설정 제거됨 - 프론트엔드에서 subject, grade, title로 이미지 렌더링

    # 원본 참조 정보 (참조용만)
    original_service = Column(String(20), nullable=False)   # "korean", "math", "english"
    original_worksheet_id = Column(Integer, nullable=False)

    # 통계
    view_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)

    # 리뷰 통계 (자동 계산)
    total_reviews = Column(Integer, default=0)
    recommend_count = Column(Integer, default=0)
    normal_count = Column(Integer, default=0)
    not_recommend_count = Column(Integer, default=0)
    satisfaction_rate = Column(Float, default=0.0)  # recommend_count / total_reviews * 100

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

    # 리뷰 내용 (단순화)
    rating = Column(String(20), nullable=False)  # 'recommend', 'normal', 'not-recommend'
    # comment 제거 - 텍스트 리뷰 없음

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    product = relationship("MarketProduct", back_populates="reviews")


# 유틸리티 함수들
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


# validate_preview_problems 함수 제거됨 - 미리보기 기능 사용 안함


# ==================== 간단한 포인트 시스템 ====================

class PointTransactionType(str, enum.Enum):
    CHARGE = "charge"           # 포인트 충전
    PURCHASE = "purchase"       # 상품 구매 (차감)
    EARN = "earn"              # 판매 수익 (적립)
    ADMIN_ADJUST = "admin_adjust"  # 관리자 조정


class UserPoint(Base):
    """사용자 포인트 관리"""
    __tablename__ = "user_points"
    __table_args__ = {"schema": "market_service"}

    user_id = Column(Integer, primary_key=True, index=True)  # auth-service의 user_id

    # 포인트 잔액
    available_points = Column(Integer, default=0)       # 사용 가능 포인트

    # 통계 (선택사항)
    total_earned = Column(Integer, default=0)          # 총 판매 수익
    total_spent = Column(Integer, default=0)           # 총 구매 금액
    total_charged = Column(Integer, default=0)         # 총 충전 금액

    # 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PointTransaction(Base):
    """포인트 거래 내역"""
    __tablename__ = "point_transactions"
    __table_args__ = {"schema": "market_service"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # 거래 정보
    transaction_type = Column(String(20), nullable=False)  # PointTransactionType
    amount = Column(Integer, nullable=False)              # 포인트 양 (+ or -)
    balance_after = Column(Integer, nullable=False)       # 거래 후 잔액

    # 연관 정보
    product_id = Column(Integer, nullable=True)           # 상품 관련 거래 시
    description = Column(String(200), nullable=False)     # 거래 설명

    # 시간
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==================== 포인트 시스템 유틸리티 ====================

PLATFORM_FEE_RATE = 0.1  # 플랫폼 수수료 10%

def calculate_seller_earning(sale_amount: int) -> tuple:
    """판매 수익 계산"""
    platform_fee = int(sale_amount * PLATFORM_FEE_RATE)
    seller_earning = sale_amount - platform_fee
    return seller_earning, platform_fee
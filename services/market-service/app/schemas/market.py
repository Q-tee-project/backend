from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from decimal import Decimal


# 미리보기 문제 스키마 제거됨 - 프론트엔드에서 subject, grade, title로 이미지 렌더링


class MarketProductBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="상품명")
    description: Optional[str] = Field(None, description="상품 설명")


class MarketProductCreate(MarketProductBase):
    # 원본 워크시트 정보
    original_service: Literal["korean", "math", "english"] = Field(..., description="원본 서비스")
    original_worksheet_id: int = Field(..., description="원본 문제지 ID")

    # 미리보기 문제 기능 제거됨


class MarketProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="상품명")
    description: Optional[str] = Field(None, description="상품 설명")
    # 미리보기 문제 기능 제거됨


class MarketProductResponse(MarketProductBase):
    id: int
    price: int  # 1500 or 3000

    # 판매자 정보
    seller_id: int
    seller_name: str

    # 원본 워크시트 정보
    worksheet_title: str
    problem_count: int
    school_level: str
    grade: int
    subject_type: str
    semester: Optional[str] = None
    unit_info: Optional[str] = None
    tags: List[str]

    # 미리보기 문제 기능 제거됨

    # 원본 참조
    original_service: str
    original_worksheet_id: int

    # 통계
    view_count: int
    purchase_count: int
    total_revenue: int
    total_reviews: int
    satisfaction_rate: float

    # 시간
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MarketProductListResponse(BaseModel):
    id: int
    title: str
    price: int
    seller_name: str
    subject_type: str
    tags: List[str]
    problem_count: int
    school_level: str
    grade: int
    # 미리보기 문제 기능 제거됨 - subject, grade, title로 이미지 생성
    satisfaction_rate: float
    view_count: int
    purchase_count: int
    total_revenue: int
    created_at: datetime

    class Config:
        from_attributes = True


class MarketPurchaseCreate(BaseModel):
    product_id: int
    # 포인트 결제만 지원


class MarketPurchaseResponse(BaseModel):
    id: int
    product_id: int
    product_title: str
    seller_name: str
    buyer_id: int
    buyer_name: str
    purchase_price: int
    payment_method: str = "points"  # 항상 포인트
    payment_status: str
    subject_type: str
    tags: List[str]
    purchased_at: datetime

    class Config:
        from_attributes = True


class MarketReviewCreate(BaseModel):
    product_id: int
    rating: Literal["recommend", "normal", "not-recommend"] = Field(..., description="평가: 추천/보통/추천안함")


class MarketReviewResponse(BaseModel):
    id: int
    product_id: int
    reviewer_id: int
    reviewer_name: str
    rating: str  # "recommend", "normal", "not-recommend"
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewStats(BaseModel):
    satisfaction_rate: float
    total_reviews: int
    breakdown: Dict[str, Dict[str, int]]  # {"recommend": {"count": 459, "percentage": 92}}


class MarketStats(BaseModel):
    total_products: int
    total_purchases: int
    total_revenue: int  # 포인트
    by_subject: dict
    recent_products: List[MarketProductListResponse]


# ==================== 포인트 시스템 스키마 ====================

class UserPointResponse(BaseModel):
    """사용자 포인트 정보"""
    user_id: int
    available_points: int
    total_earned: int
    total_spent: int
    total_charged: int

    class Config:
        from_attributes = True


class PointChargeRequest(BaseModel):
    """포인트 충전 요청"""
    amount: int = Field(..., gt=0, le=100000, description="충전할 포인트 (1~100,000)")

    @validator('amount')
    def validate_amount(cls, v):
        # 1000 포인트 단위로만 충전 가능
        if v % 1000 != 0:
            raise ValueError('1,000 포인트 단위로만 충전 가능합니다.')
        return v


class PointTransactionResponse(BaseModel):
    """포인트 거래 내역"""
    id: int
    user_id: int
    transaction_type: str
    amount: int
    balance_after: int
    product_id: Optional[int] = None
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseWithPointsRequest(BaseModel):
    """포인트로 상품 구매"""
    product_id: int


class PurchaseWithPointsResponse(BaseModel):
    """포인트 구매 결과"""
    purchase_id: int
    product_id: int
    points_spent: int
    remaining_points: int
    seller_earned: int
    platform_fee: int

    class Config:
        from_attributes = True


class SellerRevenueResponse(BaseModel):
    """판매자 수익 정보"""
    seller_id: int
    total_earned: int
    total_sales: int
    pending_points: int  # 아직 정산되지 않은 포인트
    available_points: int  # 사용 가능한 포인트

    class Config:
        from_attributes = True
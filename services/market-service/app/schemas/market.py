from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class MarketProductBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0, le=50000)
    subject_type: str = Field(..., description="과목 (국어, 수학, 영어)")
    tags: Optional[List[str]] = None


class MarketProductCreate(MarketProductBase):
    original_service: str = Field(..., description="원본 서비스 (korean, math, english)")
    original_worksheet_id: int = Field(..., description="원본 문제지 ID")


class MarketProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0, le=50000)
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class MarketProductResponse(MarketProductBase):
    id: int
    seller_id: int
    seller_name: str
    original_service: str
    original_worksheet_id: int
    status: str
    view_count: int
    purchase_count: int
    images: Optional[List[str]] = None
    main_image: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MarketProductListResponse(BaseModel):
    id: int
    title: str
    price: Decimal
    seller_name: str
    subject_type: str
    tags: Optional[List[str]] = None
    main_image: Optional[str] = None
    view_count: int
    purchase_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class MarketPurchaseCreate(BaseModel):
    product_id: int
    payment_method: Optional[str] = "free"


class MarketPurchaseResponse(BaseModel):
    id: int
    product_id: int
    buyer_id: int
    buyer_name: str
    purchase_price: Decimal
    payment_method: Optional[str]
    payment_status: str
    purchased_at: datetime

    class Config:
        from_attributes = True


class MarketReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class MarketReviewResponse(BaseModel):
    id: int
    product_id: int
    reviewer_id: int
    reviewer_name: str
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MarketStats(BaseModel):
    total_products: int
    total_purchases: int
    total_revenue: Decimal
    by_subject: dict
    recent_products: List[MarketProductListResponse]
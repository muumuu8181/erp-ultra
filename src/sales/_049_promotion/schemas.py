from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from shared.types import BaseSchema
from .models import PromotionType


class PromotionUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    end_date: Optional[date] = None


class PromotionCreate(BaseSchema):
    code: str
    name: str
    description: Optional[str] = None
    promotion_type: PromotionType
    value: Decimal
    product_codes: List[str]
    customer_groups: List[str]
    start_date: date
    end_date: date
    max_redemptions: Optional[int] = None
    is_active: bool


class PromotionResponse(BaseSchema):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    promotion_type: PromotionType
    value: Decimal
    product_codes: List[str]
    customer_groups: List[str]
    start_date: date
    end_date: date
    max_redemptions: Optional[int] = None
    current_redemptions: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PromotionRedemptionResponse(BaseSchema):
    id: int
    promotion_id: int
    order_number: str
    customer_code: str
    redeemed_value: Decimal
    redeemed_at: datetime


class PromotionRedeemRequest(BaseSchema):
    order_number: str
    customer_code: str
    redeemed_value: Decimal


class CartItem(BaseSchema):
    product_code: str
    quantity: Decimal
    unit_price: Decimal


class PromotionEvaluateRequest(BaseSchema):
    cart_items: List[CartItem]
    customer_code: str
    customer_group: Optional[str] = None


class ApplicablePromotion(BaseSchema):
    promotion_id: int
    code: str
    name: str
    promotion_type: PromotionType
    discount_value: Decimal


class PromotionEvaluateResponse(BaseSchema):
    applicable_promotions: List[ApplicablePromotion]
    best_promotion: Optional[ApplicablePromotion] = None
    total_savings: Decimal

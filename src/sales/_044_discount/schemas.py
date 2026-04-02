from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from shared.types import BaseSchema
from src.sales._044_discount.models import DiscountType, AppliesTo

class DiscountRuleCreate(BaseSchema):
    name: str
    code: str
    discount_type: DiscountType
    value: Decimal
    applies_to: AppliesTo
    product_code: Optional[str] = None
    product_category: Optional[str] = None
    customer_group: Optional[str] = None
    min_order_amount: Optional[Decimal] = None
    start_date: date
    end_date: date
    max_uses: Optional[int] = None
    is_stackable: bool
    is_active: bool

class DiscountRuleResponse(BaseSchema):
    id: int
    name: str
    code: str
    discount_type: DiscountType
    value: Decimal
    applies_to: AppliesTo
    product_code: Optional[str] = None
    product_category: Optional[str] = None
    customer_group: Optional[str] = None
    min_order_amount: Optional[Decimal] = None
    start_date: date
    end_date: date
    max_uses: Optional[int] = None
    current_uses: int
    is_stackable: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DiscountUsageResponse(BaseSchema):
    id: int
    rule_id: int
    order_number: str
    customer_code: str
    discount_amount: Decimal
    used_at: datetime

class OrderLine(BaseSchema):
    product_code: str
    quantity: Decimal
    unit_price: Decimal

class DiscountApplyRequest(BaseSchema):
    order_lines: list[OrderLine]
    customer_code: str
    customer_group: Optional[str] = None
    order_total: Decimal

class AppliedDiscount(BaseSchema):
    rule_id: int
    code: str
    name: str
    discount_amount: Decimal

class DiscountApplyResponse(BaseSchema):
    applied_discounts: list[AppliedDiscount]
    total_discount: Decimal
    final_total: Decimal

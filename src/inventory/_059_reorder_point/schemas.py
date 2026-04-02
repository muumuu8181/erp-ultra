from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from enum import Enum

from pydantic import Field

from shared.types import BaseSchema


class ReviewCycleEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AlertStatusEnum(str, Enum):
    PENDING = "pending"
    ORDERED = "ordered"
    RESOLVED = "resolved"


class ReorderPointCreate(BaseSchema):
    """Request body for creating a reorder point"""
    product_code: str = Field(..., max_length=50)
    warehouse_code: str = Field(..., max_length=50)
    reorder_point: Decimal = Field(..., decimal_places=3)
    safety_stock: Decimal = Field(..., decimal_places=3)
    reorder_quantity: Decimal = Field(..., decimal_places=3)
    lead_time_days: int
    review_cycle: ReviewCycleEnum
    is_active: bool = True
    last_reviewed: Optional[date] = None


class ReorderPointUpdate(BaseSchema):
    """Request body for updating a reorder point"""
    reorder_point: Optional[Decimal] = Field(None, decimal_places=3)
    safety_stock: Optional[Decimal] = Field(None, decimal_places=3)
    reorder_quantity: Optional[Decimal] = Field(None, decimal_places=3)
    lead_time_days: Optional[int] = None
    review_cycle: Optional[ReviewCycleEnum] = None
    is_active: Optional[bool] = None
    last_reviewed: Optional[date] = None


class ReorderPointResponse(BaseSchema):
    """Full reorder point response"""
    id: int
    product_code: str
    warehouse_code: str
    reorder_point: Decimal
    safety_stock: Decimal
    reorder_quantity: Decimal
    lead_time_days: int
    review_cycle: ReviewCycleEnum
    is_active: bool
    last_reviewed: Optional[date]
    created_at: datetime
    updated_at: datetime


class ReorderAlertResponse(BaseSchema):
    """Reorder alert with current stock and deficit info"""
    id: int
    product_code: str
    warehouse_code: str
    current_stock: Decimal
    reorder_point: Decimal
    deficit: Decimal
    status: AlertStatusEnum
    generated_at: datetime
    resolved_at: Optional[datetime]


class ReorderSuggestion(BaseSchema):
    """Suggested reorder quantity with rationale"""
    suggested_quantity: Decimal
    rationale: str

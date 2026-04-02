"""
Pydantic schemas for Sales Commission module.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import ConfigDict

from shared.types import BaseSchema, PaginatedResponse
from shared.schema import RowStatus

class CommissionCreate(BaseSchema):
    """Schema for creating a commission."""
    salesperson_id: int
    sales_order_id: int
    commission_rate: Decimal
    amount: Decimal
    currency: str = "JPY"
    status: str = RowStatus.ACTIVE
    calculation_date: date

class CommissionUpdate(BaseSchema):
    """Schema for updating a commission."""
    salesperson_id: Optional[int] = None
    sales_order_id: Optional[int] = None
    commission_rate: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    calculation_date: Optional[date] = None

class CommissionResponse(BaseSchema):
    """Schema for returning a commission."""
    id: int
    salesperson_id: int
    sales_order_id: int
    commission_rate: Decimal
    amount: Decimal
    currency: str
    status: str
    calculation_date: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

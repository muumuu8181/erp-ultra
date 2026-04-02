from typing import Optional
import datetime
from decimal import Decimal

from pydantic import Field

from shared.types import BaseSchema
from shared.schema import ColLen

class PriceListCreate(BaseSchema):
    """Request schema for creating a price list."""
    name: str = Field(..., min_length=1, max_length=ColLen.NAME)
    code: str = Field(..., min_length=1, max_length=ColLen.CODE)
    valid_from: datetime.date
    valid_to: Optional[datetime.date] = None
    currency_code: str = Field("JPY", max_length=ColLen.CURRENCY)
    is_active: bool = True

class PriceListResponse(BaseSchema):
    """Response schema for a price list."""
    id: int
    name: str
    code: str
    valid_from: datetime.date
    valid_to: Optional[datetime.date] = None
    currency_code: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class PriceListItemCreate(BaseSchema):
    """Request schema for creating a price list item."""
    product_code: str = Field(..., min_length=1, max_length=ColLen.CODE)
    unit_price: Decimal = Field(..., gt=0)
    discount_percentage: Decimal = Field(0, ge=0, le=100)
    min_quantity: Decimal = Field(1, gt=0)

class PriceListItemResponse(BaseSchema):
    """Response schema for a price list item."""
    id: int
    price_list_id: int
    product_code: str
    unit_price: Decimal
    discount_percentage: Decimal
    min_quantity: Decimal
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class PriceLookupRequest(BaseSchema):
    """Request schema for looking up a price."""
    product_code: str = Field(..., min_length=1, max_length=ColLen.CODE)
    quantity: Decimal = Field(1, gt=0)
    date: Optional[datetime.date] = None  # Defaults to today
    price_list_id: Optional[int] = None  # If None, search all active lists

class DuplicateRequest(BaseSchema):
    """Request schema for duplicating a price list."""
    new_code: str = Field(..., min_length=1, max_length=ColLen.CODE)
    new_name: Optional[str] = Field(default=None, max_length=ColLen.NAME)

class PriceLookupResponse(BaseSchema):
    """Response schema for a price lookup result."""
    product_code: str
    price_list_id: int
    price_list_code: str
    unit_price: Decimal
    discount_percentage: Decimal
    effective_price: Decimal  # unit_price * (1 - discount/100)
    min_quantity: Decimal
    quantity: Decimal
    total_price: Decimal  # effective_price * quantity
    currency_code: str

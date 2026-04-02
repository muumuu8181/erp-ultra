"""
Sales Forecast Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from shared.types import BaseSchema, DocumentStatus

class SalesForecastItemBase(BaseSchema):
    """Base schema for SalesForecastItem."""
    product_id: int
    expected_quantity: Decimal
    expected_revenue: Decimal

class SalesForecastItemCreate(SalesForecastItemBase):
    """Schema for creating a SalesForecastItem."""
    pass

class SalesForecastItemUpdate(BaseSchema):
    """Schema for updating a SalesForecastItem."""
    id: Optional[int] = None
    product_id: int
    expected_quantity: Optional[Decimal] = None
    expected_revenue: Optional[Decimal] = None

class SalesForecastItemResponse(SalesForecastItemBase):
    """Schema for SalesForecastItem response."""
    id: int
    forecast_id: int
    created_at: datetime
    updated_at: datetime


class SalesForecastBase(BaseSchema):
    """Base schema for SalesForecast."""
    period_start: date
    period_end: date
    status: DocumentStatus = DocumentStatus.DRAFT
    notes: Optional[str] = None

class SalesForecastCreate(SalesForecastBase):
    """Schema for creating a SalesForecast."""
    items: list[SalesForecastItemCreate]

class SalesForecastUpdate(BaseSchema):
    """Schema for updating a SalesForecast."""
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    status: Optional[DocumentStatus] = None
    notes: Optional[str] = None
    items: Optional[list[SalesForecastItemUpdate]] = None

class SalesForecastResponse(SalesForecastBase):
    """Schema for SalesForecast response."""
    id: int
    code: str
    total_expected_revenue: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[SalesForecastItemResponse]

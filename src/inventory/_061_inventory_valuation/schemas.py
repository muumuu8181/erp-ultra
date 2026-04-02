"""
Pydantic schemas for inventory valuation.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import Field

from shared.types import BaseSchema


class ValuationMethodCreate(BaseSchema):
    """Request body for setting a valuation method."""
    product_code: str = Field(..., max_length=50)
    method: Literal["fifo", "lifo", "weighted_average", "standard_cost", "moving_average"]
    effective_from: date
    standard_cost: Optional[Decimal] = None


class ValuationMethodResponse(BaseSchema):
    """Valuation method response."""
    id: int
    product_code: str
    method: str
    effective_from: date
    is_active: bool
    standard_cost: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class ValuationSnapshotResponse(BaseSchema):
    """Snapshot with date, product, value."""
    id: int
    snapshot_date: date
    product_code: str
    warehouse_code: str
    quantity: Decimal
    unit_cost: Decimal
    total_value: Decimal
    method: str
    calculated_at: datetime
    created_at: datetime


class CostLayerCreate(BaseSchema):
    """Request body to add a cost layer."""
    product_code: str = Field(..., max_length=50)
    warehouse_code: str = Field(..., max_length=50)
    received_date: date
    quantity: Decimal
    unit_cost: Decimal


class CostLayerResponse(BaseSchema):
    """Cost layer with remaining quantity."""
    id: int
    product_code: str
    warehouse_code: str
    received_date: date
    quantity: Decimal
    remaining_quantity: Decimal
    unit_cost: Decimal
    layer_number: int
    created_at: datetime
    updated_at: datetime


class ValuationReportItem(BaseSchema):
    """Individual item in a valuation report."""
    product_code: str
    warehouse_code: Optional[str] = None
    category: Optional[str] = None
    quantity: Decimal
    total_value: Decimal


class ValuationReport(BaseSchema):
    """Report by product/warehouse/category."""
    items: list[ValuationReportItem]
    total_value: Decimal


class ValuationSummaryItem(BaseSchema):
    """Summary item aggregated by method."""
    method: str
    total_items: int
    total_value: Decimal


class ValuationSummary(BaseSchema):
    """Aggregated valuation summary with totals."""
    total_items: int
    total_value: Decimal
    by_method: list[ValuationSummaryItem]


class CalculateValuationRequest(BaseSchema):
    """Request to calculate current valuation."""
    product_code: str
    warehouse_code: Optional[str] = None


class ConsumeCostLayerRequest(BaseSchema):
    """Request to consume cost layers."""
    product_code: str
    warehouse_code: str
    quantity: Decimal


class GenerateSnapshotRequest(BaseSchema):
    """Request to generate snapshot."""
    snapshot_date: Optional[date] = None

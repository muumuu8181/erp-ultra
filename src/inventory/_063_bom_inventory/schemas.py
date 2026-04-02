"""
Pydantic schemas for BOM and BOMItem.
"""
from typing import Optional
from datetime import datetime
from pydantic import Field

from shared.types import BaseSchema


class BOMItemCreate(BaseSchema):
    component_id: str = Field(..., max_length=50)
    quantity_required: int = Field(..., gt=0)
    uom: str = Field("pcs", max_length=20)


class BOMCreate(BaseSchema):
    product_id: str = Field(..., max_length=50)
    quantity: int = Field(1, gt=0)
    status: str = Field("active", max_length=30)
    version: int = Field(1, ge=1)
    notes: Optional[str] = Field(None, max_length=500)


class BOMItemResponse(BaseSchema):
    id: int
    bom_id: int
    component_id: str
    quantity_required: int
    uom: str
    created_at: datetime
    updated_at: datetime


class BOMResponse(BaseSchema):
    id: int
    product_id: str
    quantity: int
    status: str
    version: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class BOMWithItemsResponse(BOMResponse):
    items: list[BOMItemResponse] = []

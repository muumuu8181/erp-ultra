"""
Unit of Measure schemas.
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import Field

from shared.types import BaseSchema, PaginatedResponse


class UomType(str, Enum):
    count = "count"
    weight = "weight"
    volume = "volume"
    length = "length"
    time = "time"
    area = "area"


from shared.schema import ColLen

class UomCreate(BaseSchema):
    """Request schema for creating a unit of measure."""
    code: str = Field(..., min_length=1, max_length=ColLen.CODE)
    name: str = Field(..., min_length=1, max_length=ColLen.NAME)
    symbol: str = Field(..., min_length=1, max_length=ColLen.STATUS)
    uom_type: UomType
    decimal_places: int = Field(0, ge=0, le=6)
    is_active: bool = True


class UomResponse(BaseSchema):
    """Response schema for a unit of measure."""
    id: int
    code: str
    name: str
    symbol: str
    uom_type: str
    decimal_places: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UomConversionCreate(BaseSchema):
    """Request schema for creating a UOM conversion."""
    from_uom_id: int = Field(..., gt=0)
    to_uom_id: int = Field(..., gt=0)
    factor: Decimal = Field(..., gt=0)
    is_standard: bool = False


class UomConversionResponse(BaseSchema):
    """Response schema for a UOM conversion."""
    id: int
    from_uom_id: int
    to_uom_id: int
    factor: Decimal
    is_standard: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UomConvertRequest(BaseSchema):
    """Request schema for converting between units."""
    from_uom_id: int = Field(..., gt=0)
    to_uom_id: int = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)


class UomConvertResponse(BaseSchema):
    """Response schema for a unit conversion result."""
    from_uom_id: int
    to_uom_id: int
    input_quantity: Decimal
    converted_quantity: Decimal
    factor_used: Decimal
    conversion_path: list[str]

    class Config:
        from_attributes = True

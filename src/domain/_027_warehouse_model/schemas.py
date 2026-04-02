from shared.types import BaseSchema, PaginatedResponse
from shared.schema import ColLen
from pydantic import Field
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

class WarehouseType(str, Enum):
    own = "own"
    consignment = "consignment"
    virtual = "virtual"

class ZoneType(str, Enum):
    receiving = "receiving"
    storage = "storage"
    picking = "picking"
    shipping = "shipping"
    staging = "staging"

class TemperatureZone(str, Enum):
    ambient = "ambient"
    refrigerated = "refrigerated"
    frozen = "frozen"

class WarehouseCreate(BaseSchema):
    """Request schema for creating a warehouse."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    type: WarehouseType
    postal_code: Optional[str] = Field(None, max_length=8)
    prefecture: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    street: Optional[str] = Field(None, max_length=200)
    manager_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=ColLen.PHONE)
    is_active: bool = True

class WarehouseUpdate(BaseSchema):
    """Request schema for updating a warehouse."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[WarehouseType] = None
    postal_code: Optional[str] = Field(None, max_length=8)
    prefecture: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    street: Optional[str] = Field(None, max_length=200)
    manager_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=ColLen.PHONE)
    is_active: Optional[bool] = None

class WarehouseResponse(BaseSchema):
    """Response schema for a warehouse."""
    id: int
    code: str
    name: str
    type: str
    postal_code: Optional[str]
    prefecture: Optional[str]
    city: Optional[str]
    street: Optional[str]
    manager_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ZoneCreate(BaseSchema):
    """Request schema for creating a warehouse zone."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    zone_type: ZoneType
    temperature_zone: TemperatureZone = TemperatureZone.ambient
    is_active: bool = True

class ZoneResponse(BaseSchema):
    """Response schema for a warehouse zone."""
    id: int
    warehouse_id: int
    code: str
    name: str
    zone_type: str
    temperature_zone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BinCreate(BaseSchema):
    """Request schema for creating a bin location."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    row: Optional[str] = Field(None, max_length=10)
    column: Optional[str] = Field(None, max_length=10)
    level: Optional[str] = Field(None, max_length=10)
    capacity: Optional[Decimal] = Field(None, gt=0)
    current_usage: Optional[Decimal] = Field(0, ge=0)
    is_active: bool = True

class BinResponse(BaseSchema):
    """Response schema for a bin location."""
    id: int
    zone_id: int
    code: str
    name: str
    row: Optional[str]
    column: Optional[str]
    level: Optional[str]
    capacity: Optional[Decimal]
    current_usage: Optional[Decimal]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ZoneLayoutResponse(ZoneResponse):
    """Response schema for a zone including nested bins."""
    bins: list[BinResponse]

class WarehouseLayoutResponse(BaseSchema):
    """Response schema for full warehouse layout."""
    warehouse: WarehouseResponse
    zones: list[ZoneLayoutResponse]

from datetime import datetime
from typing import Any, Optional

from shared.types import BaseSchema


class InventoryReportBase(BaseSchema):
    """Base schema for Inventory Report properties."""
    code: str
    name: str
    description: Optional[str] = None
    report_type: str
    parameters: Optional[dict[str, Any]] = None
    status: str = "draft"


class InventoryReportCreate(InventoryReportBase):
    """Schema for creating a new Inventory Report."""
    pass


class InventoryReportUpdate(BaseSchema):
    """Schema for updating an existing Inventory Report."""
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    report_type: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class InventoryReportResponse(InventoryReportBase):
    """Schema for Inventory Report responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

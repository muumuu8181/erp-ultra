from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.types import BaseSchema

class ShipmentItemCreate(BaseSchema):
    """Schema for creating a shipment line item."""
    product_id: int
    quantity: Decimal

class ShipmentItemResponse(BaseSchema):
    """Schema for returning a shipment line item."""
    id: int
    shipment_id: int
    product_id: int
    quantity: Decimal
    created_at: datetime
    updated_at: datetime

class ShipmentCreate(BaseSchema):
    """Schema for creating a shipment header."""
    sales_order_id: int
    customer_id: int
    status: str = "draft"
    carrier: Optional[str] = None
    expected_delivery_at: Optional[datetime] = None
    items: list[ShipmentItemCreate] = []

class ShipmentUpdate(BaseSchema):
    """Schema for updating an existing shipment."""
    status: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    shipped_at: Optional[datetime] = None
    expected_delivery_at: Optional[datetime] = None

class ShipmentResponse(BaseSchema):
    """Schema for returning a shipment header."""
    id: int
    sales_order_id: int
    customer_id: int
    status: str
    tracking_number: Optional[str]
    carrier: Optional[str]
    shipped_at: Optional[datetime]
    expected_delivery_at: Optional[datetime]
    items: list[ShipmentItemResponse] = []
    created_at: datetime
    updated_at: datetime

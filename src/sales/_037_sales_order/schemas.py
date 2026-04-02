"""
Sales Order Schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from shared.types import BaseSchema, DocumentStatus, PaginatedResponse


class SalesOrderItemCreate(BaseSchema):
    """Schema for creating a sales order item."""
    product_id: int
    quantity: Decimal
    unit_price: Decimal


class SalesOrderItemResponse(BaseSchema):
    """Schema for returning a sales order item."""
    id: int
    sales_order_id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime


class SalesOrderCreate(BaseSchema):
    """Schema for creating a new sales order."""
    customer_id: int
    items: List[SalesOrderItemCreate]


class SalesOrderUpdate(BaseSchema):
    """Schema for updating a sales order."""
    status: DocumentStatus


class SalesOrderResponse(BaseSchema):
    """Schema for returning a sales order."""
    id: int
    code: str
    customer_id: int
    status: str
    total_amount: Decimal
    items: List[SalesOrderItemResponse]
    created_at: datetime
    updated_at: datetime


class SalesOrderPaginatedResponse(PaginatedResponse[SalesOrderResponse]):
    """Paginated response for sales orders."""
    pass

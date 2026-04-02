"""
Stock Transfer schemas.
"""
from datetime import date, datetime
from typing import List, Optional

from shared.types import BaseSchema


class TransferLineCreate(BaseSchema):
    """Schema for creating a stock transfer line."""
    line_number: int
    product_code: str
    product_name: str
    quantity: float
    lot_number: Optional[str] = None


class StockTransferCreate(BaseSchema):
    """Schema for creating a stock transfer."""
    transfer_number: str
    from_warehouse: str
    to_warehouse: str
    transfer_date: date
    notes: Optional[str] = None
    created_by: str
    lines: List[TransferLineCreate]


class StockTransferUpdate(BaseSchema):
    """Schema for updating a stock transfer."""
    notes: Optional[str] = None


class StockTransferLineResponse(BaseSchema):
    """Schema for a stock transfer line in response."""
    id: int
    transfer_id: int
    line_number: int
    product_code: str
    product_name: str
    quantity: float
    lot_number: Optional[str] = None
    received_quantity: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class StockTransferResponse(BaseSchema):
    """Schema for a stock transfer in response."""
    id: int
    transfer_number: str
    from_warehouse: str
    to_warehouse: str
    transfer_date: date
    status: str
    notes: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    lines: List[StockTransferLineResponse]


class ReceiveLineInput(BaseSchema):
    """Input schema for receiving a line."""
    line_id: int
    received_quantity: float

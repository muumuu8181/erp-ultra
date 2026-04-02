"""
Stock Transfer validators.
"""
from typing import List

from shared.errors import ValidationError
from src.inventory._053_stock_transfer.models import StockTransfer
from src.inventory._053_stock_transfer.schemas import ReceiveLineInput, StockTransferCreate


def validate_stock_transfer_create(data: StockTransferCreate) -> None:
    """Validate stock transfer creation rules."""
    if data.from_warehouse == data.to_warehouse:
        raise ValidationError("from_warehouse must not equal to_warehouse", field="to_warehouse")

    for line in data.lines:
        if line.quantity <= 0:
            raise ValidationError("quantity must be > 0 on all lines", field="quantity")


def validate_can_update(transfer: StockTransfer) -> None:
    """Validate if a transfer can be updated."""
    if transfer.status != "draft":
        raise ValidationError("Can only update transfers in 'draft' status", field="status")


def validate_can_cancel(transfer: StockTransfer) -> None:
    """Validate if a transfer can be cancelled."""
    if transfer.status != "draft":
        raise ValidationError("Can only cancel transfers in 'draft' status", field="status")


def validate_can_dispatch(transfer: StockTransfer) -> None:
    """Validate if a transfer can be dispatched."""
    if transfer.status != "draft":
        raise ValidationError("Can only dispatch transfers in 'draft' status", field="status")


def validate_can_receive(transfer: StockTransfer) -> None:
    """Validate if a transfer can be received."""
    if transfer.status != "in_transit":
        raise ValidationError("Can only receive transfers in 'in_transit' status", field="status")


def validate_receive_lines(transfer: StockTransfer, received_lines: List[ReceiveLineInput]) -> None:
    """Validate received quantities."""
    lines_by_id = {line.id: line for line in transfer.lines}

    for recv in received_lines:
        line = lines_by_id.get(recv.line_id)
        if not line:
            raise ValidationError(f"Line {recv.line_id} not found in transfer", field="line_id")

        if recv.received_quantity < 0:
            raise ValidationError("received_quantity cannot be negative", field="received_quantity")

        if recv.received_quantity > line.quantity:
            raise ValidationError("received_quantity must be <= quantity", field="received_quantity")

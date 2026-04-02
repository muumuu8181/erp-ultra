"""
Tests for Stock Transfer validators.
"""
from datetime import date

import pytest

from shared.errors import ValidationError
from src.inventory._053_stock_transfer.models import StockTransfer, StockTransferLine
from src.inventory._053_stock_transfer.schemas import ReceiveLineInput, StockTransferCreate, TransferLineCreate
from src.inventory._053_stock_transfer.validators import (
    validate_can_cancel,
    validate_can_dispatch,
    validate_can_receive,
    validate_can_update,
    validate_receive_lines,
    validate_stock_transfer_create,
)


def test_validate_from_warehouse_not_equal_to_warehouse():
    data = StockTransferCreate(
        transfer_number="TRF-001",
        from_warehouse="WH-A",
        to_warehouse="WH-A",
        transfer_date=date(2024, 1, 1),
        created_by="user1",
        lines=[TransferLineCreate(line_number=1, product_code="P1", product_name="P1", quantity=10)]
    )
    with pytest.raises(ValidationError, match="from_warehouse must not equal to_warehouse"):
        validate_stock_transfer_create(data)


def test_validate_quantity_greater_than_zero():
    data = StockTransferCreate(
        transfer_number="TRF-001",
        from_warehouse="WH-A",
        to_warehouse="WH-B",
        transfer_date=date(2024, 1, 1),
        created_by="user1",
        lines=[TransferLineCreate(line_number=1, product_code="P1", product_name="P1", quantity=0)]
    )
    with pytest.raises(ValidationError, match="quantity must be > 0 on all lines"):
        validate_stock_transfer_create(data)


def test_validate_can_update():
    t = StockTransfer(status="in_transit")
    with pytest.raises(ValidationError, match="Can only update transfers in 'draft' status"):
        validate_can_update(t)


def test_validate_can_cancel():
    t = StockTransfer(status="in_transit")
    with pytest.raises(ValidationError, match="Can only cancel transfers in 'draft' status"):
        validate_can_cancel(t)


def test_validate_can_dispatch():
    t = StockTransfer(status="in_transit")
    with pytest.raises(ValidationError, match="Can only dispatch transfers in 'draft' status"):
        validate_can_dispatch(t)


def test_validate_can_receive():
    t = StockTransfer(status="draft")
    with pytest.raises(ValidationError, match="Can only receive transfers in 'in_transit' status"):
        validate_can_receive(t)


def test_validate_receive_lines():
    t = StockTransfer(
        status="in_transit",
        lines=[StockTransferLine(id=1, quantity=10)]
    )

    # Valid
    validate_receive_lines(t, [ReceiveLineInput(line_id=1, received_quantity=5)])

    # Invalid quantity
    with pytest.raises(ValidationError, match="received_quantity must be <= quantity"):
        validate_receive_lines(t, [ReceiveLineInput(line_id=1, received_quantity=15)])

    # Negative quantity
    with pytest.raises(ValidationError, match="received_quantity cannot be negative"):
        validate_receive_lines(t, [ReceiveLineInput(line_id=1, received_quantity=-1)])

    # Invalid line id
    with pytest.raises(ValidationError, match="Line 99 not found in transfer"):
        validate_receive_lines(t, [ReceiveLineInput(line_id=99, received_quantity=5)])

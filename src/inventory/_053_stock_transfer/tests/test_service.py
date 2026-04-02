"""
Tests for Stock Transfer service.
"""
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import BusinessRuleError, NotFoundError, ValidationError
from src.inventory._053_stock_transfer.schemas import (
    ReceiveLineInput,
    StockTransferCreate,
    StockTransferUpdate,
    TransferLineCreate,
)
from src.inventory._053_stock_transfer.service import (
    cancel_transfer,
    create_transfer,
    dispatch,
    get_in_transit,
    get_transfer,
    list_transfers,
    receive_transfer,
    update_transfer,
)


@pytest.fixture
def create_data():
    return StockTransferCreate(
        transfer_number="TRF-100",
        from_warehouse="WH-1",
        to_warehouse="WH-2",
        transfer_date=date(2024, 1, 1),
        created_by="user1",
        lines=[
            TransferLineCreate(line_number=1, product_code="P1", product_name="P1", quantity=10),
            TransferLineCreate(line_number=2, product_code="P2", product_name="P2", quantity=20),
        ]
    )


@pytest.mark.asyncio
async def test_create_transfer(db_session: AsyncSession, create_data):
    transfer = await create_transfer(db_session, create_data)

    assert transfer.id is not None
    assert transfer.status == "draft"
    assert len(transfer.lines) == 2


@pytest.mark.asyncio
async def test_create_transfer_same_warehouse(db_session: AsyncSession, create_data):
    create_data.to_warehouse = create_data.from_warehouse
    with pytest.raises(ValidationError):
        await create_transfer(db_session, create_data)


@pytest.mark.asyncio
async def test_update_transfer(db_session: AsyncSession, create_data):
    transfer = await create_transfer(db_session, create_data)

    updated = await update_transfer(db_session, transfer.id, StockTransferUpdate(notes="Updated notes"))
    assert updated.notes == "Updated notes"


@pytest.mark.asyncio
async def test_dispatch(db_session: AsyncSession, create_data):
    transfer = await create_transfer(db_session, create_data)

    dispatched = await dispatch(db_session, transfer.id)
    assert dispatched.status == "in_transit"


@pytest.mark.asyncio
async def test_dispatch_already_dispatched(db_session: AsyncSession, create_data):
    transfer = await create_transfer(db_session, create_data)
    await dispatch(db_session, transfer.id)

    with pytest.raises(BusinessRuleError):
        await dispatch(db_session, transfer.id)


@pytest.mark.asyncio
async def test_receive_transfer_valid(db_session: AsyncSession, create_data):
    transfer = await create_transfer(db_session, create_data)

    # Reload to ensure lines are properly attached in the same session
    transfer = await get_transfer(db_session, transfer.id)
    line1_id = transfer.lines[0].id
    line2_id = transfer.lines[1].id

    await dispatch(db_session, transfer.id)

    recv_inputs = [
        ReceiveLineInput(line_id=line1_id, received_quantity=5),
        ReceiveLineInput(line_id=line2_id, received_quantity=20),
    ]

    received = await receive_transfer(db_session, transfer.id, recv_inputs)

    # Reload with lines to test lazy loading behavior correctly
    received = await get_transfer(db_session, received.id)

    assert received.status == "received"
    assert received.lines[0].received_quantity == 5
    assert received.lines[1].received_quantity == 20


@pytest.mark.asyncio
async def test_receive_transfer_quantity_gt_sent(db_session: AsyncSession, create_data):
    transfer = await create_transfer(db_session, create_data)

    transfer = await get_transfer(db_session, transfer.id)
    line1_id = transfer.lines[0].id

    await dispatch(db_session, transfer.id)

    recv_inputs = [
        ReceiveLineInput(line_id=line1_id, received_quantity=15),
    ]

    with pytest.raises(ValidationError):
        await receive_transfer(db_session, transfer.id, recv_inputs)


@pytest.mark.asyncio
async def test_cancel_transfer(db_session: AsyncSession, create_data):
    transfer = await create_transfer(db_session, create_data)
    cancelled = await cancel_transfer(db_session, transfer.id, reason="Changed mind")

    assert cancelled.status == "cancelled"
    assert "Changed mind" in cancelled.notes


@pytest.mark.asyncio
async def test_cancel_transfer_in_transit(db_session: AsyncSession, create_data):
    transfer = await create_transfer(db_session, create_data)
    await dispatch(db_session, transfer.id)

    with pytest.raises(BusinessRuleError):
        await cancel_transfer(db_session, transfer.id)


@pytest.mark.asyncio
async def test_list_transfers(db_session: AsyncSession, create_data):
    await create_transfer(db_session, create_data)

    res = await list_transfers(db_session, from_warehouse="WH-1")
    assert res.total == 1
    assert len(res.items) == 1

    res2 = await list_transfers(db_session, to_warehouse="WH-X")
    assert res2.total == 0


@pytest.mark.asyncio
async def test_get_transfer_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await get_transfer(db_session, 9999)


@pytest.mark.asyncio
async def test_get_in_transit(db_session: AsyncSession, create_data):
    transfer1 = await create_transfer(db_session, create_data)
    await dispatch(db_session, transfer1.id)

    create_data2 = create_data.copy()
    create_data2.transfer_number = "TRF-101"
    create_data2.from_warehouse = "WH-3"
    create_data2.to_warehouse = "WH-4"
    transfer2 = await create_transfer(db_session, create_data2)
    await dispatch(db_session, transfer2.id)

    res = await get_in_transit(db_session)
    assert len(res) == 2

    res_wh1 = await get_in_transit(db_session, warehouse_code="WH-1")
    assert len(res_wh1) == 1
    assert res_wh1[0].id == transfer1.id

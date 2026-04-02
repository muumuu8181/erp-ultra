"""
Tests for Stock Transfer models.
"""
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.inventory._053_stock_transfer.models import StockTransfer, StockTransferLine


@pytest.mark.asyncio
async def test_create_stock_transfer(db_session: AsyncSession):
    transfer = StockTransfer(
        transfer_number="TRF-001",
        from_warehouse="WH-A",
        to_warehouse="WH-B",
        transfer_date=date(2024, 1, 1),
        status="draft",
        notes="Test notes",
        created_by="user1"
    )

    line = StockTransferLine(
        line_number=1,
        product_code="PROD-1",
        product_name="Product 1",
        quantity=10.5,
        lot_number="LOT-001"
    )
    transfer.lines.append(line)

    db_session.add(transfer)
    await db_session.commit()
    await db_session.refresh(transfer)

    # ensure it's fetched correctly in session by accessing id directly
    # instead of doing transfer.lines which might trigger lazy loading
    transfer_id = transfer.id
    assert transfer_id is not None
    assert transfer.transfer_number == "TRF-001"

    # Reload with selectinload to test the lazy loading correctly on lines
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    stmt = select(StockTransfer).options(selectinload(StockTransfer.lines)).where(StockTransfer.id == transfer_id)
    res = await db_session.execute(stmt)
    loaded_transfer = res.scalar_one()

    assert len(loaded_transfer.lines) == 1
    assert loaded_transfer.lines[0].id is not None
    assert loaded_transfer.lines[0].transfer_id == transfer_id
    assert loaded_transfer.lines[0].received_quantity is None


@pytest.mark.asyncio
async def test_unique_transfer_number(db_session: AsyncSession):
    t1 = StockTransfer(
        transfer_number="TRF-002",
        from_warehouse="WH-A",
        to_warehouse="WH-B",
        transfer_date=date(2024, 1, 1),
        status="draft",
        created_by="user1"
    )
    db_session.add(t1)
    await db_session.commit()

    t2 = StockTransfer(
        transfer_number="TRF-002",
        from_warehouse="WH-B",
        to_warehouse="WH-C",
        transfer_date=date(2024, 1, 2),
        status="draft",
        created_by="user1"
    )
    db_session.add(t2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

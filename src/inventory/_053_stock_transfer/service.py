"""
Stock Transfer service.
"""
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.errors import BusinessRuleError, NotFoundError, ValidationError
from shared.types import PaginatedResponse
from src.inventory._053_stock_transfer.models import StockTransfer, StockTransferLine
from src.inventory._053_stock_transfer.schemas import (
    ReceiveLineInput,
    StockTransferCreate,
    StockTransferUpdate,
)
from src.inventory._053_stock_transfer.validators import (
    validate_can_cancel,
    validate_can_dispatch,
    validate_can_receive,
    validate_can_update,
    validate_receive_lines,
    validate_stock_transfer_create,
)


async def create_transfer(db: AsyncSession, data: StockTransferCreate) -> StockTransfer:
    """Create a new stock transfer."""
    validate_stock_transfer_create(data)

    # Check unique transfer_number
    stmt = select(StockTransfer).where(StockTransfer.transfer_number == data.transfer_number)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise ValidationError("transfer_number must be unique", field="transfer_number")

    transfer = StockTransfer(
        transfer_number=data.transfer_number,
        from_warehouse=data.from_warehouse,
        to_warehouse=data.to_warehouse,
        transfer_date=data.transfer_date,
        status="draft",
        notes=data.notes,
        created_by=data.created_by,
    )

    for line_data in data.lines:
        line = StockTransferLine(
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            quantity=line_data.quantity,
            lot_number=line_data.lot_number,
        )
        transfer.lines.append(line)

    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)

    # Reload with lines
    stmt_reload = select(StockTransfer).options(
        selectinload(StockTransfer.lines)
    ).where(StockTransfer.id == transfer.id)
    res = await db.execute(stmt_reload)
    return res.scalar_one()


async def get_transfer(db: AsyncSession, transfer_id: int) -> StockTransfer:
    """Get a stock transfer by ID."""
    stmt = select(StockTransfer).options(selectinload(StockTransfer.lines)).where(StockTransfer.id == transfer_id)
    result = await db.execute(stmt)
    transfer = result.scalar_one_or_none()

    if not transfer:
        raise NotFoundError("StockTransfer", str(transfer_id))

    return transfer


async def update_transfer(db: AsyncSession, transfer_id: int, data: StockTransferUpdate) -> StockTransfer:
    """Update a stock transfer."""
    transfer = await get_transfer(db, transfer_id)
    validate_can_update(transfer)

    if data.notes is not None:
        transfer.notes = data.notes

    await db.commit()
    await db.refresh(transfer)
    return transfer


async def dispatch(db: AsyncSession, transfer_id: int) -> StockTransfer:
    """Dispatch a stock transfer."""
    transfer = await get_transfer(db, transfer_id)

    # Using BusinessRuleError as per test requirements
    if transfer.status != "draft":
        raise BusinessRuleError("Can only dispatch transfers in 'draft' status")

    validate_can_dispatch(transfer)

    # Stub check: validate from_warehouse has sufficient stock
    # In a real app, this would query inventory balances

    transfer.status = "in_transit"
    await db.commit()
    await db.refresh(transfer)
    return transfer


async def receive_transfer(db: AsyncSession, transfer_id: int, received_lines: List[ReceiveLineInput]) -> StockTransfer:
    """Receive a stock transfer."""
    transfer = await get_transfer(db, transfer_id)

    validate_can_receive(transfer)
    validate_receive_lines(transfer, received_lines)

    lines_by_id = {line.id: line for line in transfer.lines}

    # Record received quantities per line
    for recv in received_lines:
        line = lines_by_id[recv.line_id]
        line.received_quantity = recv.received_quantity

    # In a real app, we might check if ALL lines were fully or partially received
    # and only then set status to "received".
    # For this requirement: "Transition status: in_transit -> received when all lines received"

    # Check if all lines have a received_quantity
    all_received = all(line.received_quantity is not None for line in transfer.lines)
    if all_received:
        transfer.status = "received"

    await db.commit()
    await db.refresh(transfer)
    return transfer


async def cancel_transfer(db: AsyncSession, transfer_id: int, reason: Optional[str] = None) -> StockTransfer:
    """Cancel a stock transfer."""
    transfer = await get_transfer(db, transfer_id)

    if transfer.status != "draft":
        raise BusinessRuleError("Can only cancel transfers in 'draft' status")

    validate_can_cancel(transfer)

    transfer.status = "cancelled"
    if reason:
        transfer.notes = (transfer.notes or "") + f"\nCancel reason: {reason}"

    await db.commit()
    await db.refresh(transfer)
    return transfer


async def list_transfers(
    db: AsyncSession,
    from_warehouse: Optional[str] = None,
    to_warehouse: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
) -> PaginatedResponse:
    """List stock transfers with pagination and filters."""
    stmt = select(StockTransfer)

    if from_warehouse:
        stmt = stmt.where(StockTransfer.from_warehouse == from_warehouse)
    if to_warehouse:
        stmt = stmt.where(StockTransfer.to_warehouse == to_warehouse)
    if status:
        stmt = stmt.where(StockTransfer.status == status)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Pagination
    stmt = stmt.options(selectinload(StockTransfer.lines))
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def get_in_transit(db: AsyncSession, warehouse_code: Optional[str] = None) -> List[StockTransfer]:
    """Get all transfers currently in_transit."""
    stmt = select(StockTransfer).options(selectinload(StockTransfer.lines)).where(StockTransfer.status == "in_transit")

    if warehouse_code:
        # In-transit query filters by either from or to warehouse
        stmt = stmt.where(
            (StockTransfer.from_warehouse == warehouse_code) |
            (StockTransfer.to_warehouse == warehouse_code)
        )

    result = await db.execute(stmt)
    return list(result.scalars().all())

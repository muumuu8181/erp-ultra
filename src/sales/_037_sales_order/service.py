"""
Sales Order Service
"""
import math
from typing import Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.errors import NotFoundError
from shared.types import CodeGenerator, DocumentStatus
from src.sales._037_sales_order.models import SalesOrder, SalesOrderItem
from src.sales._037_sales_order.schemas import SalesOrderCreate, SalesOrderUpdate
from src.sales._037_sales_order.validators import validate_sales_order_create


async def create_sales_order(db: AsyncSession, data: SalesOrderCreate) -> SalesOrder:
    """
    Create a new sales order along with its items.
    """
    validate_sales_order_create(data)

    total_amount = sum((item.quantity * item.unit_price for item in data.items))

    order_code = CodeGenerator.generate("SO")

    sales_order = SalesOrder(
        code=order_code,
        customer_id=data.customer_id,
        status=DocumentStatus.DRAFT.value,
        total_amount=total_amount,
    )

    db.add(sales_order)
    await db.flush()

    for item_data in data.items:
        item = SalesOrderItem(
            sales_order_id=sales_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
        )
        db.add(item)

    await db.commit()
    await db.refresh(sales_order)

    # Reload with relationships
    return await get_sales_order(db, sales_order.id)


async def get_sales_order(db: AsyncSession, order_id: int) -> SalesOrder:
    """
    Retrieve a sales order by ID.
    """
    stmt = select(SalesOrder).options(selectinload(SalesOrder.items)).where(SalesOrder.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundError("SalesOrder", str(order_id))

    return order


async def list_sales_orders(
    db: AsyncSession, page: int = 1, page_size: int = 50
) -> Tuple[list[SalesOrder], int, int, int]:
    """
    List sales orders with pagination.
    """
    skip = (page - 1) * page_size

    count_stmt = select(func.count()).select_from(SalesOrder)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = select(SalesOrder).options(selectinload(SalesOrder.items)).offset(skip).limit(page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return items, total, page, total_pages


async def update_sales_order_status(
    db: AsyncSession, order_id: int, data: SalesOrderUpdate
) -> SalesOrder:
    """
    Update the status of a sales order.
    """
    order = await get_sales_order(db, order_id)

    order.status = data.status.value
    await db.commit()
    await db.refresh(order)

    return order


async def delete_sales_order(db: AsyncSession, order_id: int) -> None:
    """
    Delete a sales order.
    """
    order = await get_sales_order(db, order_id)
    await db.delete(order)
    await db.commit()

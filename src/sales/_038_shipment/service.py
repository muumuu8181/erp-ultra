from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func

from src.sales._038_shipment.models import Shipment, ShipmentItem
from src.sales._038_shipment.schemas import ShipmentCreate, ShipmentUpdate
from src.sales._038_shipment.validators import validate_shipment_create, validate_shipment_update
from shared.errors import NotFoundError

async def create_shipment(db: AsyncSession, data: ShipmentCreate) -> Shipment:
    """Creates a new shipment and its line items."""
    validate_shipment_create(data)

    shipment = Shipment(
        sales_order_id=data.sales_order_id,
        customer_id=data.customer_id,
        status=data.status,
        carrier=data.carrier,
        expected_delivery_at=data.expected_delivery_at
    )

    for item_data in data.items:
        shipment.items.append(ShipmentItem(
            product_id=item_data.product_id,
            quantity=item_data.quantity
        ))

    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)

    # Reload with items eager loaded
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.items))
        .where(Shipment.id == shipment.id)
    )
    return result.scalar_one()

async def get_shipment(db: AsyncSession, shipment_id: int) -> Shipment:
    """Retrieves a shipment by ID."""
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.items))
        .where(Shipment.id == shipment_id)
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise NotFoundError(f"Shipment with ID {shipment_id} not found.")
    return shipment

async def get_shipments(db: AsyncSession, skip: int = 0, limit: int = 100) -> tuple[Sequence[Shipment], int]:
    """Retrieves a paginated list of shipments."""
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.items))
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()

    total_result = await db.execute(select(func.count(Shipment.id)))
    total = total_result.scalar_one()

    return items, total

async def update_shipment(db: AsyncSession, shipment_id: int, data: ShipmentUpdate) -> Shipment:
    """Updates an existing shipment."""
    validate_shipment_update(data)
    shipment = await get_shipment(db, shipment_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(shipment, key, value)

    db.add(shipment)
    await db.commit()

    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.items))
        .where(Shipment.id == shipment.id)
    )
    return result.scalar_one()

async def delete_shipment(db: AsyncSession, shipment_id: int) -> None:
    """Deletes a shipment."""
    shipment = await get_shipment(db, shipment_id)
    await db.delete(shipment)
    await db.commit()

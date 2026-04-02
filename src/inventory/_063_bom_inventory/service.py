"""
Business logic for BOM inventory module.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shared.errors import NotFoundError, ValidationError
from src.inventory._063_bom_inventory.models import BOM, BOMItem
from src.inventory._063_bom_inventory.schemas import BOMCreate, BOMItemCreate
from src.inventory._063_bom_inventory.validators import validate_positive_quantity, validate_circular_dependency


async def create_bom(db: AsyncSession, bom_in: BOMCreate) -> BOM:
    """Creates a new BOM."""
    validate_positive_quantity(bom_in.quantity)
    bom = BOM(**bom_in.model_dump())
    db.add(bom)
    await db.commit()
    await db.refresh(bom)
    return bom


async def get_bom(db: AsyncSession, bom_id: int) -> BOM:
    """Retrieves a BOM by ID with its items."""
    stmt = select(BOM).options(selectinload(BOM.items)).where(BOM.id == bom_id)
    result = await db.execute(stmt)
    bom = result.scalar_one_or_none()
    if bom is None:
        raise NotFoundError("BOM", str(bom_id))
    return bom


async def list_boms(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[BOM]:
    """Retrieves a list of BOMs."""
    stmt = select(BOM).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_bom(db: AsyncSession, bom_id: int, bom_in: BOMCreate) -> BOM:
    """Updates an existing BOM."""
    validate_positive_quantity(bom_in.quantity)
    bom = await get_bom(db, bom_id)

    update_data = bom_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bom, key, value)

    await db.commit()
    await db.refresh(bom)
    return bom


async def delete_bom(db: AsyncSession, bom_id: int) -> None:
    """Deletes a BOM and its items."""
    bom = await get_bom(db, bom_id)
    await db.delete(bom)
    await db.commit()


async def add_bom_item(db: AsyncSession, bom_id: int, item_in: BOMItemCreate) -> BOMItem:
    """Adds a component item to an existing BOM."""
    validate_positive_quantity(item_in.quantity_required)

    # Check if bom exists
    bom = await get_bom(db, bom_id)

    # Check for circular dependency
    await validate_circular_dependency(db, bom.product_id, item_in.component_id)

    item = BOMItem(bom_id=bom_id, **item_in.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def remove_bom_item(db: AsyncSession, bom_id: int, item_id: int) -> None:
    """Removes a component item from a BOM."""
    stmt = select(BOMItem).where(BOMItem.id == item_id, BOMItem.bom_id == bom_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item is None:
        raise NotFoundError("BOMItem", str(item_id))

    await db.delete(item)
    await db.commit()

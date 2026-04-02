from shared.errors import ValidationError, NotFoundError, DuplicateError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from src.domain._027_warehouse_model.models import Warehouse, WarehouseZone, BinLocation

def validate_warehouse_code_unique(value: str) -> str:
    """Validate warehouse code format.

    Args:
        value: The warehouse code string.
    Returns:
        The validated code.
    Raises:
        ValidationError: If code format is invalid.
    """
    if not value or not value.strip():
        raise ValidationError("Warehouse code cannot be empty.")
    # Assuming valid code logic here (can be simple length or pattern)
    return value.strip()

async def validate_warehouse_exists(db: AsyncSession, warehouse_id: int) -> None:
    """Validate that a warehouse exists.

    Args:
        db: Database session.
        warehouse_id: Warehouse ID to check.
    Raises:
        NotFoundError: If warehouse does not exist.
    """
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Warehouse not found.")

async def validate_zone_exists(db: AsyncSession, zone_id: int) -> None:
    """Validate that a zone exists.

    Args:
        db: Database session.
        zone_id: Zone ID to check.
    Raises:
        NotFoundError: If zone does not exist.
    """
    stmt = select(WarehouseZone).where(WarehouseZone.id == zone_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise NotFoundError("Zone not found.")

async def validate_bin_code_unique_in_zone(db: AsyncSession, zone_id: int, code: str, exclude_id: Optional[int] = None) -> None:
    """Validate bin code is unique within its zone.

    Args:
        db: Database session.
        zone_id: Zone ID.
        code: Bin code to check.
        exclude_id: Bin ID to exclude (for updates).
    Raises:
        DuplicateError: If a bin with the same code already exists in the zone.
    """
    stmt = select(BinLocation).where(BinLocation.zone_id == zone_id, BinLocation.code == code)
    if exclude_id is not None:
        stmt = stmt.where(BinLocation.id != exclude_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise DuplicateError("A bin with this code already exists in the zone.")

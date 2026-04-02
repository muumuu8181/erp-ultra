from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Optional, Any
import math

from src.domain._027_warehouse_model.models import Warehouse, WarehouseZone, BinLocation
from src.domain._027_warehouse_model.schemas import (
    WarehouseCreate, WarehouseUpdate, ZoneCreate, BinCreate, WarehouseLayoutResponse,
    WarehouseResponse, ZoneResponse, BinResponse
)
from shared.types import PaginatedResponse
from shared.errors import NotFoundError, DuplicateError, ValidationError
from src.domain._027_warehouse_model.validators import (
    validate_warehouse_exists, validate_zone_exists, validate_bin_code_unique_in_zone
)


async def create_warehouse(db: AsyncSession, data: WarehouseCreate) -> Warehouse:
    """Create a new warehouse.

    Args:
        db: Database session.
        data: Warehouse creation data.
    Returns:
        The created Warehouse record.
    Raises:
        DuplicateError: If a warehouse with the same code already exists.
    """
    stmt = select(Warehouse).where(Warehouse.code == data.code)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise DuplicateError("Warehouse with this code already exists.")

    warehouse = Warehouse(**data.model_dump())
    db.add(warehouse)
    await db.flush()
    await db.refresh(warehouse)
    return warehouse


async def update_warehouse(db: AsyncSession, warehouse_id: int, data: WarehouseUpdate) -> Warehouse:
    """Update an existing warehouse.

    Args:
        db: Database session.
        warehouse_id: ID of the warehouse to update.
        data: Warehouse update data (partial).
    Returns:
        The updated Warehouse record.
    Raises:
        NotFoundError: If the warehouse does not exist.
    """
    await validate_warehouse_exists(db, warehouse_id)

    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    result = await db.execute(stmt)
    warehouse = result.scalar_one()

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(warehouse, key, value)

    await db.flush()
    await db.refresh(warehouse)
    return warehouse


async def get_warehouse(db: AsyncSession, warehouse_id: int) -> Warehouse:
    """Get a warehouse by ID.

    Args:
        db: Database session.
        warehouse_id: ID of the warehouse.
    Returns:
        The Warehouse record.
    Raises:
        NotFoundError: If the warehouse does not exist.
    """
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    result = await db.execute(stmt)
    warehouse = result.scalar_one_or_none()
    if warehouse is None:
        raise NotFoundError("Warehouse not found.")
    return warehouse


async def list_warehouses(
    db: AsyncSession, is_active: Optional[bool] = None, page: int = 1, page_size: int = 50
) -> PaginatedResponse[WarehouseResponse]:
    """List warehouses with optional filtering.

    Args:
        db: Database session.
        is_active: Optional filter by active status.
        page: Page number.
        page_size: Items per page.
    Returns:
        PaginatedResponse containing WarehouseResponse items.
    """
    stmt = select(Warehouse)
    if is_active is not None:
        stmt = stmt.where(Warehouse.is_active == is_active)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return PaginatedResponse[WarehouseResponse](
        items=[WarehouseResponse.model_validate(w) for w in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 1
    )


async def create_zone(db: AsyncSession, warehouse_id: int, data: ZoneCreate) -> WarehouseZone:
    """Create a zone within a warehouse.

    Args:
        db: Database session.
        warehouse_id: ID of the parent warehouse.
        data: Zone creation data.
    Returns:
        The created WarehouseZone record.
    Raises:
        NotFoundError: If the warehouse does not exist.
        DuplicateError: If a zone with the same code already exists in the warehouse.
    """
    await validate_warehouse_exists(db, warehouse_id)

    stmt = select(WarehouseZone).where(
        WarehouseZone.warehouse_id == warehouse_id,
        WarehouseZone.code == data.code
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise DuplicateError("Zone with this code already exists in the warehouse.")

    zone = WarehouseZone(warehouse_id=warehouse_id, **data.model_dump())
    db.add(zone)
    await db.flush()
    await db.refresh(zone)
    return zone


async def list_zones(
    db: AsyncSession, warehouse_id: int, page: int = 1, page_size: int = 50
) -> PaginatedResponse[ZoneResponse]:
    """List zones for a warehouse.

    Args:
        db: Database session.
        warehouse_id: ID of the warehouse.
        page: Page number.
        page_size: Items per page.
    Returns:
        PaginatedResponse containing ZoneResponse items.
    """
    stmt = select(WarehouseZone).where(WarehouseZone.warehouse_id == warehouse_id)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return PaginatedResponse[ZoneResponse](
        items=[ZoneResponse.model_validate(z) for z in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 1
    )


async def create_bin(db: AsyncSession, zone_id: int, data: BinCreate) -> BinLocation:
    """Create a bin location within a zone.

    Args:
        db: Database session.
        zone_id: ID of the parent zone.
        data: Bin creation data.
    Returns:
        The created BinLocation record.
    Raises:
        NotFoundError: If the zone does not exist.
        DuplicateError: If a bin with the same code already exists in the zone.
        ValidationError: If current_usage > capacity.
    """
    await validate_zone_exists(db, zone_id)
    await validate_bin_code_unique_in_zone(db, zone_id, data.code)

    if data.capacity is not None and data.current_usage is not None:
        if data.current_usage > data.capacity:
            raise ValidationError("Current usage cannot exceed capacity.")

    bin_loc = BinLocation(zone_id=zone_id, **data.model_dump())
    db.add(bin_loc)
    await db.flush()
    await db.refresh(bin_loc)
    return bin_loc


async def list_bins(
    db: AsyncSession, zone_id: int, page: int = 1, page_size: int = 50
) -> PaginatedResponse[BinResponse]:
    """List bin locations for a zone.

    Args:
        db: Database session.
        zone_id: ID of the zone.
        page: Page number.
        page_size: Items per page.
    Returns:
        PaginatedResponse containing BinResponse items.
    """
    stmt = select(BinLocation).where(BinLocation.zone_id == zone_id)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return PaginatedResponse[BinResponse](
        items=[BinResponse.model_validate(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 1
    )


async def get_warehouse_layout(db: AsyncSession, warehouse_id: int) -> WarehouseLayoutResponse:
    """Get the full warehouse layout (warehouse + zones + bins).

    Returns a nested structure with the warehouse, all its zones,
    and all bins within each zone.

    Args:
        db: Database session.
        warehouse_id: ID of the warehouse.
    Returns:
        WarehouseLayoutResponse with nested zone/bin data.
    Raises:
        NotFoundError: If the warehouse does not exist.
    """
    await validate_warehouse_exists(db, warehouse_id)

    w_stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    warehouse = (await db.execute(w_stmt)).scalar_one()

    z_stmt = select(WarehouseZone).where(WarehouseZone.warehouse_id == warehouse_id)
    zones = (await db.execute(z_stmt)).scalars().all()

    b_stmt = select(BinLocation).join(WarehouseZone).where(WarehouseZone.warehouse_id == warehouse_id)
    bins = (await db.execute(b_stmt)).scalars().all()

    bins_by_zone: dict[int, list[BinResponse]] = {}
    for b in bins:
        bins_by_zone.setdefault(b.zone_id, []).append(BinResponse.model_validate(b))

    from src.domain._027_warehouse_model.schemas import ZoneLayoutResponse

    zones_list = []
    for z in zones:
        z_dict = ZoneResponse.model_validate(z).model_dump()
        z_dict["bins"] = bins_by_zone.get(z.id, [])
        zones_list.append(ZoneLayoutResponse(**z_dict))

    return WarehouseLayoutResponse(
        warehouse=WarehouseResponse.model_validate(warehouse),
        zones=zones_list
    )


async def deactivate_warehouse(db: AsyncSession, warehouse_id: int) -> Warehouse:
    """Deactivate a warehouse and all its zones and bins.

    Sets is_active=False on the warehouse, all zones, and all bins.

    Args:
        db: Database session.
        warehouse_id: ID of the warehouse to deactivate.
    Returns:
        The deactivated Warehouse record.
    Raises:
        NotFoundError: If the warehouse does not exist.
    """
    await validate_warehouse_exists(db, warehouse_id)

    # Deactivate bins
    b_stmt = update(BinLocation).where(
        BinLocation.zone_id.in_(
            select(WarehouseZone.id).where(WarehouseZone.warehouse_id == warehouse_id)
        )
    ).values(is_active=False)
    await db.execute(b_stmt)

    # Deactivate zones
    z_stmt = update(WarehouseZone).where(WarehouseZone.warehouse_id == warehouse_id).values(is_active=False)
    await db.execute(z_stmt)

    # Deactivate warehouse
    w_stmt = update(Warehouse).where(Warehouse.id == warehouse_id).values(is_active=False)
    await db.execute(w_stmt)

    # Return deactivated warehouse
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    warehouse = (await db.execute(stmt)).scalar_one()

    await db.flush()
    return warehouse

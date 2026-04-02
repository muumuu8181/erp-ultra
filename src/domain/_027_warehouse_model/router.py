from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.foundation._001_database.engine import get_db
from shared.types import PaginatedResponse
from src.domain._027_warehouse_model import service
from src.domain._027_warehouse_model.schemas import (
    WarehouseCreate, WarehouseUpdate, ZoneCreate, BinCreate, WarehouseLayoutResponse,
    WarehouseResponse, ZoneResponse, BinResponse
)

router = APIRouter(prefix="/api/v1", tags=["warehouses"])


@router.post("/warehouses", response_model=WarehouseResponse, status_code=201)
async def create_warehouse(
    data: WarehouseCreate,
    db: AsyncSession = Depends(get_db)
) -> WarehouseResponse:
    """Create a new warehouse."""
    warehouse = await service.create_warehouse(db, data)
    return WarehouseResponse.model_validate(warehouse)


@router.get("/warehouses", response_model=PaginatedResponse[WarehouseResponse])
async def list_warehouses(
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[WarehouseResponse]:
    """List warehouses."""
    return await service.list_warehouses(db, is_active=is_active, page=page, page_size=page_size)


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db)
) -> WarehouseResponse:
    """Get warehouse by ID."""
    warehouse = await service.get_warehouse(db, warehouse_id)
    return WarehouseResponse.model_validate(warehouse)


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    db: AsyncSession = Depends(get_db)
) -> WarehouseResponse:
    """Update warehouse."""
    warehouse = await service.update_warehouse(db, warehouse_id, data)
    return WarehouseResponse.model_validate(warehouse)


@router.post("/warehouses/{warehouse_id}/zones", response_model=ZoneResponse, status_code=201)
async def create_zone(
    warehouse_id: int,
    data: ZoneCreate,
    db: AsyncSession = Depends(get_db)
) -> ZoneResponse:
    """Create a new zone in a warehouse."""
    zone = await service.create_zone(db, warehouse_id, data)
    return ZoneResponse.model_validate(zone)


@router.get("/warehouses/{warehouse_id}/zones", response_model=PaginatedResponse[ZoneResponse])
async def list_zones(
    warehouse_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[ZoneResponse]:
    """List zones in a warehouse."""
    return await service.list_zones(db, warehouse_id, page=page, page_size=page_size)


@router.post("/zones/{zone_id}/bins", response_model=BinResponse, status_code=201)
async def create_bin(
    zone_id: int,
    data: BinCreate,
    db: AsyncSession = Depends(get_db)
) -> BinResponse:
    """Create a new bin in a zone."""
    bin_loc = await service.create_bin(db, zone_id, data)
    return BinResponse.model_validate(bin_loc)


@router.get("/zones/{zone_id}/bins", response_model=PaginatedResponse[BinResponse])
async def list_bins(
    zone_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[BinResponse]:
    """List bins in a zone."""
    return await service.list_bins(db, zone_id, page=page, page_size=page_size)


@router.get("/warehouses/{warehouse_id}/layout", response_model=WarehouseLayoutResponse)
async def get_warehouse_layout(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db)
) -> WarehouseLayoutResponse:
    """Get the full warehouse layout."""
    return await service.get_warehouse_layout(db, warehouse_id)

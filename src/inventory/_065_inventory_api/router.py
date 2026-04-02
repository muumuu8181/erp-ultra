from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from foundation._001_database.engine import get_db
from shared.types import PaginatedResponse
from .schemas import InventoryEndpointResponse, InventoryEndpointCreate, InventoryEndpointUpdate
from . import service

router = APIRouter(prefix="/api/v1/inventory-api", tags=["inventory-api"])


@router.post("/", response_model=InventoryEndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    endpoint_in: InventoryEndpointCreate,
    db: AsyncSession = Depends(get_db)
) -> InventoryEndpointResponse:
    """
    Create a new inventory API endpoint.
    """
    return await service.create_inventory_endpoint(db, endpoint_in)


@router.get("/", response_model=PaginatedResponse[InventoryEndpointResponse])
async def list_endpoints(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[InventoryEndpointResponse]:
    """
    Retrieve a paginated list of inventory endpoints.
    """
    return await service.get_inventory_endpoints(db, skip=skip, limit=limit, is_active=is_active)


from shared.errors import NotFoundError
from fastapi import HTTPException

@router.get("/{endpoint_id}", response_model=InventoryEndpointResponse)
async def get_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db)
) -> InventoryEndpointResponse:
    """
    Retrieve a specific inventory endpoint by ID.
    """
    try:
        return await service.get_inventory_endpoint(db, endpoint_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{endpoint_id}", response_model=InventoryEndpointResponse)
async def update_endpoint(
    endpoint_id: int,
    endpoint_in: InventoryEndpointUpdate,
    db: AsyncSession = Depends(get_db)
) -> InventoryEndpointResponse:
    """
    Update a specific inventory endpoint.
    """
    try:
        return await service.update_inventory_endpoint(db, endpoint_id, endpoint_in)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a specific inventory endpoint.
    """
    try:
        await service.delete_inventory_endpoint(db, endpoint_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

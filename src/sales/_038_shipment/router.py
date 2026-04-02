from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import math

from src.foundation._001_database import get_db
from src.sales._038_shipment import service
from src.sales._038_shipment.schemas import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
)
from shared.types import PaginatedResponse

router = APIRouter(prefix="/api/v1/_038_shipment", tags=["shipment"])

@router.post("/", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    shipment: ShipmentCreate,
    db: AsyncSession = Depends(get_db)
) -> ShipmentResponse:
    """Create a new shipment."""
    created = await service.create_shipment(db, shipment)
    return created

@router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(
    shipment_id: int,
    db: AsyncSession = Depends(get_db)
) -> ShipmentResponse:
    """Get a shipment by ID."""
    result = await service.get_shipment(db, shipment_id)
    return result

@router.get("/", response_model=PaginatedResponse[ShipmentResponse])
async def list_shipments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[ShipmentResponse]:
    """List shipments."""
    items, total = await service.get_shipments(db, skip=skip, limit=limit)
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1

    return PaginatedResponse[ShipmentResponse](
        items=items,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )

@router.patch("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: int,
    shipment: ShipmentUpdate,
    db: AsyncSession = Depends(get_db)
) -> ShipmentResponse:
    """Update a shipment."""
    updated = await service.update_shipment(db, shipment_id, shipment)
    return updated

@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(
    shipment_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a shipment."""
    await service.delete_shipment(db, shipment_id)

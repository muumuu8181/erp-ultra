"""
Unit of Measure API router.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from src.domain._026_unit_of_measure.schemas import (
    UomCreate, UomResponse, UomConversionCreate, UomConversionResponse,
    UomConvertRequest, UomConvertResponse
)
from src.domain._026_unit_of_measure import service
from shared.types import PaginatedResponse

router = APIRouter(prefix="/api/v1/uoms", tags=["uoms"])


@router.post("", response_model=UomResponse, status_code=status.HTTP_201_CREATED)
async def create_uom(
    data: UomCreate, db: AsyncSession = Depends(get_db)
) -> UomResponse:
    """Create a new unit of measure."""
    uom = await service.create_uom(db, data)
    return UomResponse.model_validate(uom)


@router.get("", response_model=PaginatedResponse[UomResponse])
async def list_uoms(
    uom_type: Optional[str] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[UomResponse]:
    """List units of measure."""
    return await service.list_uoms(
        db, uom_type=uom_type, is_active=is_active, page=page, page_size=page_size
    )


@router.post("/conversions", response_model=UomConversionResponse, status_code=status.HTTP_201_CREATED)
async def create_conversion(
    data: UomConversionCreate, db: AsyncSession = Depends(get_db)
) -> UomConversionResponse:
    """Create a conversion factor between two units."""
    conversion = await service.create_conversion(db, data)
    return UomConversionResponse.model_validate(conversion)


@router.get("/conversions", response_model=PaginatedResponse[UomConversionResponse])
async def list_conversions(
    uom_id: int = Query(..., description="Unit ID to get conversions for"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[UomConversionResponse]:
    """List conversions for a given unit."""
    return await service.get_conversions(db, uom_id=uom_id, page=page, page_size=page_size)


@router.post("/convert", response_model=UomConvertResponse)
async def convert_quantity(
    request: UomConvertRequest, db: AsyncSession = Depends(get_db)
) -> UomConvertResponse:
    """Convert a quantity from one unit to another."""
    return await service.convert_quantity(db, request)


@router.get("/{id}/compatible", response_model=list[UomResponse])
async def get_compatible_uoms(
    id: int, db: AsyncSession = Depends(get_db)
) -> list[UomResponse]:
    """Get all units that can be converted to/from the given unit."""
    return await service.get_compatible_uoms(db, uom_id=id)

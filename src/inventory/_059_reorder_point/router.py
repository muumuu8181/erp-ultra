from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from shared.types import PaginatedResponse
from shared.errors import (
    ValidationError as SharedValidationError,
    NotFoundError,
    DuplicateError,
    CalculationError
)
from . import service
from .schemas import (
    ReorderPointCreate,
    ReorderPointUpdate,
    ReorderPointResponse,
    ReorderAlertResponse,
    ReorderSuggestion,
    AlertStatusEnum
)

router = APIRouter(prefix="/api/v1/reorder-point", tags=["Reorder Point"])


@router.post("/reorder-points", response_model=ReorderPointResponse, status_code=status.HTTP_201_CREATED)
async def create_reorder_point(
    data: ReorderPointCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a reorder point."""
    try:
        return await service.create_reorder_point(db, data)
    except SharedValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.get("/reorder-points", response_model=PaginatedResponse[ReorderPointResponse])
async def list_reorder_points(
    warehouse_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List reorder points."""
    return await service.list_reorder_points(
        db, warehouse_code=warehouse_code, is_active=is_active, page=page, page_size=page_size
    )


@router.get("/reorder-points/{id}", response_model=ReorderPointResponse)
async def get_reorder_point(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a reorder point."""
    try:
        return await service.get_reorder_point(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.put("/reorder-points/{id}", response_model=ReorderPointResponse)
async def update_reorder_point(
    id: int,
    data: ReorderPointUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a reorder point."""
    try:
        return await service.update_reorder_point(db, id, data)
    except SharedValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.delete("/reorder-points/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reorder_point(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a reorder point."""
    try:
        await service.delete_reorder_point(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/reorder-points/check", response_model=list[ReorderAlertResponse])
async def check_reorder_points(
    warehouse_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Check reorder points against stock."""
    return await service.check_reorder_points(db, warehouse_code)


@router.post("/reorder-points/generate-alerts", response_model=list[ReorderAlertResponse])
async def generate_alerts(
    warehouse_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Generate new alerts."""
    return await service.generate_alerts(db, warehouse_code)


@router.get("/reorder-alerts", response_model=PaginatedResponse[ReorderAlertResponse])
async def list_alerts(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List alerts."""
    return await service.get_alerts(db, status=status, page=page, page_size=page_size)


@router.post("/reorder-alerts/{id}/resolve", response_model=ReorderAlertResponse)
async def resolve_alert(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert."""
    try:
        return await service.resolve_alert(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/reorder-points/{id}/safety-stock", response_class=PlainTextResponse)
async def calculate_safety_stock(
    id: int,
    demand_std_dev: Decimal = Query(..., gt=0),
    lead_time_days: int = Query(..., gt=0),
    service_level_z: Decimal = Query(Decimal("1.65"), gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Calculate safety stock."""
    try:
        result = await service.calculate_safety_stock(
            db, id, demand_std_dev, lead_time_days, service_level_z
        )
        return str(result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except CalculationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/reorder-points/{id}/suggest-quantity", response_model=ReorderSuggestion)
async def suggest_reorder_quantity(
    id: int,
    annual_demand: Optional[Decimal] = Query(None, gt=0),
    ordering_cost: Optional[Decimal] = Query(None, gt=0),
    holding_cost_pct: Optional[Decimal] = Query(None, gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Get reorder suggestion."""
    try:
        return await service.suggest_reorder_quantity(
            db, id, annual_demand, ordering_cost, holding_cost_pct
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

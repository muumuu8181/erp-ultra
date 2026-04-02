"""
Sales Forecast Router
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from shared.types import PaginatedResponse
from src.foundation._001_database.engine import get_db

from .schemas import SalesForecastCreate, SalesForecastUpdate, SalesForecastResponse
from . import service

router = APIRouter(prefix="/api/v1/sales-forecasts", tags=["sales-forecast"])

@router.post("/", response_model=SalesForecastResponse, status_code=status.HTTP_201_CREATED)
async def create_forecast(data: SalesForecastCreate, db: AsyncSession = Depends(get_db)) -> SalesForecastResponse:
    """Create a new sales forecast."""
    return await service.create_forecast(db, data)

@router.get("/", response_model=PaginatedResponse[SalesForecastResponse])
async def list_forecasts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[SalesForecastResponse]:
    """List sales forecasts with pagination."""
    return await service.list_forecasts(db, page, page_size)

@router.get("/{forecast_id}", response_model=SalesForecastResponse)
async def get_forecast(forecast_id: int, db: AsyncSession = Depends(get_db)) -> SalesForecastResponse:
    """Get a sales forecast by ID."""
    return await service.get_forecast(db, forecast_id)

@router.put("/{forecast_id}", response_model=SalesForecastResponse)
async def update_forecast(forecast_id: int, data: SalesForecastUpdate, db: AsyncSession = Depends(get_db)) -> SalesForecastResponse:
    """Update a sales forecast."""
    result = await service.update_forecast(db, forecast_id, data)
    # the ORM returns updated_at, but we need to ensure the attribute is loaded/accessible before returning to Pydantic
    # Specifically, we must load the relationship to prevent MissingGreenlet
    await db.refresh(result, attribute_names=["items", "updated_at"])
    return result

@router.delete("/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_forecast(forecast_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a sales forecast."""
    await service.delete_forecast(db, forecast_id)

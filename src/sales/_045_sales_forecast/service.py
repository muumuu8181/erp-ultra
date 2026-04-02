"""
Sales Forecast Service
"""
from typing import Sequence
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.types import CodeGenerator, PaginatedResponse
from shared.errors import NotFoundError
from .models import SalesForecast, SalesForecastItem
from .schemas import SalesForecastCreate, SalesForecastUpdate
from .validators import validate_sales_forecast_create, validate_sales_forecast_update

async def create_forecast(db: AsyncSession, data: SalesForecastCreate) -> SalesForecast:
    """Create a new sales forecast."""
    validate_sales_forecast_create(data)

    forecast = SalesForecast(
        code=CodeGenerator.generate("FC"),
        period_start=data.period_start,
        period_end=data.period_end,
        status=data.status,
        notes=data.notes,
        total_expected_revenue=sum((item.expected_revenue for item in data.items), Decimal('0.00'))
    )
    db.add(forecast)
    await db.flush()

    for item_data in data.items:
        item = SalesForecastItem(
            forecast_id=forecast.id,
            product_id=item_data.product_id,
            expected_quantity=item_data.expected_quantity,
            expected_revenue=item_data.expected_revenue,
        )
        db.add(item)

    await db.commit()
    await db.refresh(forecast, ["items"])
    return forecast

async def get_forecast(db: AsyncSession, forecast_id: int) -> SalesForecast:
    """Retrieve a sales forecast by ID."""
    result = await db.execute(
        select(SalesForecast)
        .options(selectinload(SalesForecast.items))
        .where(SalesForecast.id == forecast_id)
    )
    forecast = result.scalar_one_or_none()
    if not forecast:
        raise NotFoundError("SalesForecast", str(forecast_id))
    return forecast

async def update_forecast(db: AsyncSession, forecast_id: int, data: SalesForecastUpdate) -> SalesForecast:
    """Update a sales forecast."""
    forecast = await get_forecast(db, forecast_id)

    validate_sales_forecast_update(data, forecast.period_start, forecast.period_end)

    if data.period_start is not None:
        forecast.period_start = data.period_start
    if data.period_end is not None:
        forecast.period_end = data.period_end
    if data.status is not None:
        forecast.status = data.status
    if data.notes is not None:
        forecast.notes = data.notes

    if data.items is not None:
        # Instead of deleting directly with delete() statement, we can modify the relationship
        # to take advantage of the cascade="all, delete-orphan".
        forecast.items.clear()

        for item_data in data.items:
            item = SalesForecastItem(
                forecast_id=forecast.id,
                product_id=item_data.product_id,
                expected_quantity=item_data.expected_quantity if item_data.expected_quantity is not None else Decimal('0.000'),
                expected_revenue=item_data.expected_revenue if item_data.expected_revenue is not None else Decimal('0.00'),
            )
            forecast.items.append(item)

        forecast.total_expected_revenue = sum(
            (item.expected_revenue for item in data.items if item.expected_revenue is not None),
            Decimal('0.00')
        )

    await db.commit()
    await db.refresh(forecast, ["items"])
    return forecast

async def delete_forecast(db: AsyncSession, forecast_id: int) -> None:
    """Delete a sales forecast."""
    forecast = await get_forecast(db, forecast_id)
    await db.delete(forecast)
    await db.commit()

async def list_forecasts(db: AsyncSession, page: int = 1, page_size: int = 50) -> PaginatedResponse:
    """List sales forecasts with pagination."""
    # Count total
    count_stmt = select(func.count(SalesForecast.id))
    total = await db.scalar(count_stmt) or 0

    # Get items
    stmt = (
        select(SalesForecast)
        .options(selectinload(SalesForecast.items))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

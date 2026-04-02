"""
Sales Forecast Service Tests
"""
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from shared.errors import NotFoundError
from shared.types import DocumentStatus
from src.sales._045_sales_forecast.schemas import SalesForecastCreate, SalesForecastUpdate, SalesForecastItemCreate, SalesForecastItemUpdate
from src.sales._045_sales_forecast.service import create_forecast, get_forecast, update_forecast, delete_forecast, list_forecasts

@pytest.mark.asyncio
async def test_create_and_get_forecast(db: AsyncSession) -> None:
    """Test creating and retrieving a forecast."""
    data = SalesForecastCreate(
        period_start=date(2023, 10, 1),
        period_end=date(2023, 10, 31),
        items=[
            SalesForecastItemCreate(product_id=1, expected_quantity=Decimal('10'), expected_revenue=Decimal('100.50')),
            SalesForecastItemCreate(product_id=2, expected_quantity=Decimal('5'), expected_revenue=Decimal('50.00'))
        ]
    )
    forecast = await create_forecast(db, data)
    assert forecast.id is not None
    assert forecast.total_expected_revenue == Decimal('150.50')
    assert len(forecast.items) == 2

    fetched = await get_forecast(db, forecast.id)
    assert fetched.id == forecast.id
    assert fetched.total_expected_revenue == Decimal('150.50')

@pytest.mark.asyncio
async def test_update_forecast(db: AsyncSession) -> None:
    """Test updating a forecast."""
    data = SalesForecastCreate(
        period_start=date(2023, 10, 1),
        period_end=date(2023, 10, 31),
        items=[SalesForecastItemCreate(product_id=1, expected_quantity=Decimal('10'), expected_revenue=Decimal('100.00'))]
    )
    forecast = await create_forecast(db, data)

    update_data = SalesForecastUpdate(
        status=DocumentStatus.APPROVED,
        items=[SalesForecastItemUpdate(product_id=3, expected_quantity=Decimal('20'), expected_revenue=Decimal('200.00'))]
    )
    updated = await update_forecast(db, forecast.id, update_data)

    assert updated.status == DocumentStatus.APPROVED
    assert len(updated.items) == 1
    assert updated.items[0].product_id == 3
    assert updated.total_expected_revenue == Decimal('200.00')

@pytest.mark.asyncio
async def test_delete_forecast(db: AsyncSession) -> None:
    """Test deleting a forecast."""
    data = SalesForecastCreate(
        period_start=date(2023, 10, 1),
        period_end=date(2023, 10, 31),
        items=[SalesForecastItemCreate(product_id=1, expected_quantity=Decimal('10'), expected_revenue=Decimal('100.00'))]
    )
    forecast = await create_forecast(db, data)

    await delete_forecast(db, forecast.id)

    with pytest.raises(NotFoundError):
        await get_forecast(db, forecast.id)

@pytest.mark.asyncio
async def test_list_forecasts(db: AsyncSession) -> None:
    """Test listing forecasts."""
    data1 = SalesForecastCreate(period_start=date(2023, 10, 1), period_end=date(2023, 10, 31), items=[SalesForecastItemCreate(product_id=1, expected_quantity=Decimal('10'), expected_revenue=Decimal('100.00'))])
    data2 = SalesForecastCreate(period_start=date(2023, 11, 1), period_end=date(2023, 11, 30), items=[SalesForecastItemCreate(product_id=2, expected_quantity=Decimal('20'), expected_revenue=Decimal('200.00'))])

    await create_forecast(db, data1)
    await create_forecast(db, data2)

    paginated = await list_forecasts(db, page=1, page_size=10)
    assert paginated.total >= 2
    assert len(paginated.items) >= 2

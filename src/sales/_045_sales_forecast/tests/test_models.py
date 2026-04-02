"""
Sales Forecast Models Tests
"""
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.sales._045_sales_forecast.models import SalesForecast, SalesForecastItem

@pytest.mark.asyncio
async def test_sales_forecast_model_creation(db: AsyncSession) -> None:
    """Test creating a SalesForecast."""
    forecast = SalesForecast(
        code="FC-202310-0001",
        period_start=date(2023, 10, 1),
        period_end=date(2023, 12, 31),
        status="draft",
        total_expected_revenue=Decimal('1000.00'),
        notes="Q4 Forecast"
    )
    db.add(forecast)
    await db.commit()
    await db.refresh(forecast)

    assert forecast.id is not None
    assert forecast.code == "FC-202310-0001"
    assert forecast.period_start == date(2023, 10, 1)

@pytest.mark.asyncio
async def test_sales_forecast_item_model_creation(db: AsyncSession) -> None:
    """Test creating a SalesForecastItem linked to SalesForecast."""
    forecast = SalesForecast(
        code="FC-202311-0001",
        period_start=date(2023, 11, 1),
        period_end=date(2023, 11, 30)
    )
    db.add(forecast)
    await db.flush()

    item = SalesForecastItem(
        forecast_id=forecast.id,
        product_id=1,
        expected_quantity=Decimal('10.5'),
        expected_revenue=Decimal('500.00')
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await db.refresh(forecast, ["items"])

    assert item.id is not None
    assert item.forecast_id == forecast.id
    assert len(forecast.items) == 1
    assert forecast.items[0].expected_revenue == Decimal('500.00')

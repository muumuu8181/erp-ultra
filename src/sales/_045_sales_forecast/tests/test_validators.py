"""
Sales Forecast Validators Tests
"""
from datetime import date
from decimal import Decimal
import pytest
from shared.errors import ValidationError
from src.sales._045_sales_forecast.schemas import SalesForecastCreate, SalesForecastUpdate, SalesForecastItemCreate, SalesForecastItemUpdate
from src.sales._045_sales_forecast.validators import validate_sales_forecast_create, validate_sales_forecast_update

def test_validate_sales_forecast_create_success() -> None:
    """Test successful validation of creation."""
    data = SalesForecastCreate(
        period_start=date(2023, 10, 1),
        period_end=date(2023, 10, 31),
        items=[SalesForecastItemCreate(product_id=1, expected_quantity=Decimal('10'), expected_revenue=Decimal('100'))]
    )
    validate_sales_forecast_create(data)

def test_validate_sales_forecast_create_invalid_period() -> None:
    """Test validation fails when period_end < period_start."""
    data = SalesForecastCreate(
        period_start=date(2023, 10, 31),
        period_end=date(2023, 10, 1),
        items=[]
    )
    with pytest.raises(ValidationError, match="period_end cannot be before period_start"):
        validate_sales_forecast_create(data)

def test_validate_sales_forecast_create_negative_quantity() -> None:
    """Test validation fails on negative quantity."""
    data = SalesForecastCreate(
        period_start=date(2023, 10, 1),
        period_end=date(2023, 10, 31),
        items=[SalesForecastItemCreate(product_id=1, expected_quantity=Decimal('-1'), expected_revenue=Decimal('100'))]
    )
    with pytest.raises(ValidationError, match="expected_quantity cannot be negative"):
        validate_sales_forecast_create(data)

def test_validate_sales_forecast_update_success() -> None:
    """Test successful validation of update."""
    data = SalesForecastUpdate(
        period_start=date(2023, 10, 5),
        items=[SalesForecastItemUpdate(product_id=1, expected_quantity=Decimal('10'), expected_revenue=Decimal('100'))]
    )
    validate_sales_forecast_update(data, current_start=date(2023, 10, 1), current_end=date(2023, 10, 31))

def test_validate_sales_forecast_update_invalid_period() -> None:
    """Test validation fails when updated period is invalid."""
    data = SalesForecastUpdate(
        period_end=date(2023, 9, 30)
    )
    with pytest.raises(ValidationError, match="period_end cannot be before period_start"):
        validate_sales_forecast_update(data, current_start=date(2023, 10, 1), current_end=date(2023, 10, 31))

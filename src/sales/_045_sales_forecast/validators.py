"""
Sales Forecast Validators
"""
from decimal import Decimal
from shared.errors import ValidationError
from .schemas import SalesForecastCreate, SalesForecastUpdate

def validate_sales_forecast_create(data: SalesForecastCreate) -> None:
    """Validate SalesForecastCreate data."""
    if data.period_end < data.period_start:
        raise ValidationError("period_end cannot be before period_start", field="period_end")

    for i, item in enumerate(data.items):
        if item.expected_quantity < Decimal('0'):
            raise ValidationError("expected_quantity cannot be negative", field=f"items[{i}].expected_quantity")
        if item.expected_revenue < Decimal('0'):
            raise ValidationError("expected_revenue cannot be negative", field=f"items[{i}].expected_revenue")

from datetime import date

def validate_sales_forecast_update(data: SalesForecastUpdate, current_start: date, current_end: date) -> None:
    """Validate SalesForecastUpdate data."""
    start = data.period_start if data.period_start is not None else current_start
    end = data.period_end if data.period_end is not None else current_end

    if end < start:
        raise ValidationError("period_end cannot be before period_start", field="period_end")

    if data.items is not None:
        for i, item in enumerate(data.items):
            if item.expected_quantity is not None and item.expected_quantity < Decimal('0'):
                raise ValidationError("expected_quantity cannot be negative", field=f"items[{i}].expected_quantity")
            if item.expected_revenue is not None and item.expected_revenue < Decimal('0'):
                raise ValidationError("expected_revenue cannot be negative", field=f"items[{i}].expected_revenue")

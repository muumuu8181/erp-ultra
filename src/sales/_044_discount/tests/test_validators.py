import pytest
from datetime import date, timedelta
from decimal import Decimal
from shared.errors import ValidationError
from src.sales._044_discount.validators import validate_discount_value, validate_date_range
from src.sales._044_discount.models import DiscountType

def test_validate_discount_value_positive():
    validate_discount_value(Decimal("10.0"), DiscountType.percentage)
    validate_discount_value(Decimal("100.0"), DiscountType.fixed_amount)

def test_validate_discount_value_negative():
    with pytest.raises(ValidationError):
        validate_discount_value(Decimal("0.0"), DiscountType.fixed_amount)
    with pytest.raises(ValidationError):
        validate_discount_value(Decimal("-10.0"), DiscountType.fixed_amount)

def test_validate_discount_value_percentage_exceed():
    with pytest.raises(ValidationError):
        validate_discount_value(Decimal("101.0"), DiscountType.percentage)

def test_validate_date_range():
    start = date.today()
    end = start + timedelta(days=10)
    validate_date_range(start, end)

    with pytest.raises(ValidationError):
        validate_date_range(end, start)

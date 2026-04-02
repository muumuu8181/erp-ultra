import pytest
from decimal import Decimal
from sales._042_commission.validators import validate_commission_rate, validate_amount
from shared.errors import ValidationError

def test_validate_commission_rate_valid():
    validate_commission_rate(Decimal("10.0"))
    validate_commission_rate(Decimal("0.0"))
    validate_commission_rate(Decimal("100.0"))

def test_validate_commission_rate_invalid():
    with pytest.raises(ValidationError):
        validate_commission_rate(Decimal("-1.0"))
    with pytest.raises(ValidationError):
        validate_commission_rate(Decimal("101.0"))

def test_validate_amount_valid():
    validate_amount(Decimal("10.0"))
    validate_amount(Decimal("0.0"))

def test_validate_amount_invalid():
    with pytest.raises(ValidationError):
        validate_amount(Decimal("-1.0"))

import pytest
from datetime import date
from decimal import Decimal

from shared.errors import ValidationError
from src.domain._028_pricing.validators import (
    validate_date_range, validate_positive_price, validate_discount_percentage, validate_product_code_exists
)

def test_validate_date_range():
    # valid_from < valid_to (ok)
    validate_date_range(date(2023, 1, 1), date(2023, 12, 31))

    # valid_from == valid_to (ok)
    validate_date_range(date(2023, 1, 1), date(2023, 1, 1))

    # valid_to = None (ok)
    validate_date_range(date(2023, 1, 1), None)

    # valid_from > valid_to (raises)
    with pytest.raises(ValidationError):
        validate_date_range(date(2023, 12, 31), date(2023, 1, 1))

def test_validate_positive_price():
    # valid
    assert validate_positive_price(Decimal("100.00")) == Decimal("100.00")
    assert validate_positive_price(Decimal("0.01")) == Decimal("0.01")

    # invalid
    with pytest.raises(ValidationError):
        validate_positive_price(Decimal("0.00"))
    with pytest.raises(ValidationError):
        validate_positive_price(Decimal("-1.00"))

def test_validate_discount_percentage():
    # valid
    assert validate_discount_percentage(Decimal("0")) == Decimal("0")
    assert validate_discount_percentage(Decimal("50.00")) == Decimal("50.00")
    assert validate_discount_percentage(Decimal("100.00")) == Decimal("100.00")

    # invalid
    with pytest.raises(ValidationError):
        validate_discount_percentage(Decimal("-0.01"))
    with pytest.raises(ValidationError):
        validate_discount_percentage(Decimal("100.01"))

@pytest.mark.asyncio
async def test_validate_product_code_exists():
    class MockDB:
        pass
    db_session = MockDB()

    # valid format
    await validate_product_code_exists(db_session, "PROD-1")

    # invalid format (empty)
    with pytest.raises(ValidationError):
        await validate_product_code_exists(db_session, "")
    with pytest.raises(ValidationError):
        await validate_product_code_exists(db_session, "   ")

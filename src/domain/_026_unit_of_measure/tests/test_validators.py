"""
Tests for Unit of Measure validators.
"""
import pytest
from decimal import Decimal
from shared.errors import ValidationError
from src.domain._026_unit_of_measure.validators import (
    validate_code_unique,
    validate_factor_positive,
    validate_no_self_reference
)


def test_validate_code_unique():
    assert validate_code_unique("kg") == "KG"
    assert validate_code_unique(" PCS ") == "PCS"

    with pytest.raises(ValidationError):
        validate_code_unique("")

    with pytest.raises(ValidationError):
        validate_code_unique("   ")


def test_validate_factor_positive():
    assert validate_factor_positive(Decimal("1000.0")) == Decimal("1000.0")
    assert validate_factor_positive(Decimal("0.001")) == Decimal("0.001")

    with pytest.raises(ValidationError):
        validate_factor_positive(Decimal("0"))

    with pytest.raises(ValidationError):
        validate_factor_positive(Decimal("-1"))


@pytest.mark.asyncio
async def test_validate_no_self_reference():
    # different ids - ok
    await validate_no_self_reference(1, 2)

    with pytest.raises(ValidationError):
        await validate_no_self_reference(1, 1)

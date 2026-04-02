"""
Tests for Payment Terms validators.
"""
import pytest
from pydantic import ValidationError as PydanticValidationError
from shared.errors import ValidationError
from src.domain._029_payment_terms.schemas import PaymentTermCreate, PaymentTermUpdate
from src.domain._029_payment_terms.validators import validate_payment_term_create, validate_payment_term_update


def test_validate_create_valid():
    """Test creating with valid data."""
    data = PaymentTermCreate(code="NET30", name="Net 30 Days", days=30)
    validate_payment_term_create(data)  # Should not raise


def test_validate_create_empty_code():
    """Test creating with empty code."""
    data = PaymentTermCreate(code="   ", name="Net 30 Days", days=30)
    with pytest.raises(ValidationError) as exc:
        validate_payment_term_create(data)
    assert exc.value.field == "code"


def test_validate_create_empty_name():
    """Test creating with empty name."""
    data = PaymentTermCreate(code="NET30", name="", days=30)
    with pytest.raises(ValidationError) as exc:
        validate_payment_term_create(data)
    assert exc.value.field == "name"


def test_validate_create_negative_days():
    """Test creating with negative days."""
    with pytest.raises(PydanticValidationError) as exc:
        PaymentTermCreate(code="NET30", name="Net 30", days=-1)
    assert "Input should be greater than or equal to 0" in str(exc.value)


def test_validate_update_valid():
    """Test updating with valid data."""
    data = PaymentTermUpdate(code="NET60", days=60)
    validate_payment_term_update(data)  # Should not raise


def test_validate_update_empty_code():
    """Test updating with empty code."""
    data = PaymentTermUpdate(code="  ")
    with pytest.raises(ValidationError) as exc:
        validate_payment_term_update(data)
    assert exc.value.field == "code"


def test_validate_update_negative_days():
    """Test updating with negative days."""
    with pytest.raises(PydanticValidationError) as exc:
        PaymentTermUpdate(days=-5)
    assert "Input should be greater than or equal to 0" in str(exc.value)

import pytest
from shared.errors import ValidationError
from src.domain._016_customer_model.validators import (
    validate_customer_code,
    validate_email,
    validate_phone,
    validate_corporate_number
)

def test_validate_customer_code():
    validate_customer_code("CUS-00001")
    validate_customer_code("CUS-ABC12")

    with pytest.raises(ValidationError):
        validate_customer_code("CUS-")
    with pytest.raises(ValidationError):
        validate_customer_code("XXX-12345")
    with pytest.raises(ValidationError):
        validate_customer_code("cus-12345")
    with pytest.raises(ValidationError):
        validate_customer_code("CUS-123456")

def test_validate_email():
    validate_email("test@example.com")
    validate_email("a.b+c@d.e-f.com")

    with pytest.raises(ValidationError):
        validate_email("test@")
    with pytest.raises(ValidationError):
        validate_email("test.com")

def test_validate_phone():
    validate_phone("03-1234-5678")
    validate_phone("090-1234-5678")
    validate_phone("0123-45-6789")

    with pytest.raises(ValidationError):
        validate_phone("123-456-7890")
    with pytest.raises(ValidationError):
        validate_phone("090-123-4567")
    with pytest.raises(ValidationError):
        validate_phone("03-1234-56789")

def test_validate_corporate_number():
    validate_corporate_number("1234567890122")

    with pytest.raises(ValidationError):
        validate_corporate_number("1234567890123")  # wrong check digit

    with pytest.raises(ValidationError):
        validate_corporate_number("123456789012")  # wrong length

    with pytest.raises(ValidationError):
        validate_corporate_number("123456789012A")  # non-numeric

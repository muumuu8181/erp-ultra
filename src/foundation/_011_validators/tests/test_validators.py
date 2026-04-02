import pytest
from datetime import date
from src.foundation._011_validators.validators import (
    validate_japanese_phone,
    validate_postal_code,
    validate_email,
    validate_date_range,
    check_japanese_phone,
    check_postal_code,
    check_email
)

def test_validate_japanese_phone():
    assert validate_japanese_phone("090-1234-5678") is True
    assert validate_japanese_phone("03-1234-5678") is True
    assert validate_japanese_phone("09012345678") is True
    assert validate_japanese_phone("invalid") is False
    assert validate_japanese_phone("123-456-7890") is False # Invalid JP phone format

def test_validate_postal_code():
    assert validate_postal_code("123-4567") is True
    assert validate_postal_code("1234567") is True
    assert validate_postal_code("12-34567") is False

def test_validate_email():
    assert validate_email("test@example.com") is True
    assert validate_email("invalid-email") is False

def test_validate_date_range():
    assert validate_date_range(date(2023, 1, 1), date(2023, 1, 2)) is True
    assert validate_date_range(date(2023, 1, 2), date(2023, 1, 2)) is True
    assert validate_date_range(date(2023, 1, 3), date(2023, 1, 2)) is False

def test_pydantic_validators():
    assert check_japanese_phone("090-1234-5678") == "090-1234-5678"
    with pytest.raises(ValueError):
        check_japanese_phone("invalid")

    assert check_postal_code("123-4567") == "123-4567"
    with pytest.raises(ValueError):
        check_postal_code("invalid")

    assert check_email("test@example.com") == "test@example.com"
    with pytest.raises(ValueError):
        check_email("invalid")

import re
from datetime import date
from typing import Any

from shared.errors import ValidationError


def validate_japanese_phone(phone: str) -> bool:
    """
    Validate a Japanese phone number format (hyphens optional).
    Valid formats: 090-1234-5678, 03-1234-5678, 09012345678, etc.
    """
    pattern = re.compile(r"^(0\d{1,4}-?\d{1,4}-?\d{4})$")
    return bool(pattern.match(phone))


def validate_postal_code(postal_code: str) -> bool:
    """
    Validate Japanese postal code format (XXX-XXXX or XXXXXXX).
    """
    pattern = re.compile(r"^\d{3}-?\d{4}$")
    return bool(pattern.match(postal_code))


def validate_email(email: str) -> bool:
    """
    Basic email format validation.
    """
    pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    return bool(pattern.match(email))


def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Validate that start_date is before or equal to end_date.
    """
    return start_date <= end_date


# Pydantic AfterValidator helpers
def check_japanese_phone(v: Any) -> Any:
    if not isinstance(v, str):
        raise ValueError("Phone must be a string")
    if not validate_japanese_phone(v):
        raise ValueError("Invalid Japanese phone number format")
    return v


def check_postal_code(v: Any) -> Any:
    if not isinstance(v, str):
        raise ValueError("Postal code must be a string")
    if not validate_postal_code(v):
        raise ValueError("Invalid Japanese postal code format")
    return v


def check_email(v: Any) -> Any:
    if not isinstance(v, str):
        raise ValueError("Email must be a string")
    if not validate_email(v):
        raise ValueError("Invalid email format")
    return v

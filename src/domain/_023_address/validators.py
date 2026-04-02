"""
Validation logic for Address Book module.
"""
import re
from shared.errors import ValidationError
from .schemas import AddressCreate, AddressUpdate


def validate_postal_code(postal_code: str) -> None:
    """
    Validate Japanese postal code format (e.g., 123-4567 or 1234567).

    Args:
        postal_code: The postal code to validate.

    Raises:
        ValidationError: If the postal code is invalid.
    """
    # Allows 7 digits with an optional hyphen after the 3rd digit
    pattern = r"^\d{3}-?\d{4}$"
    if not re.match(pattern, postal_code):
        raise ValidationError(
            message="Invalid Japanese postal code format. Expected 'NNN-NNNN' or 'NNNNNNN'.",
            field="postal_code"
        )


def validate_address_create(schema: AddressCreate) -> None:
    """
    Validate AddressCreate schema.
    """
    validate_postal_code(schema.postal_code)


def validate_address_update(schema: AddressUpdate) -> None:
    """
    Validate AddressUpdate schema.
    """
    if schema.postal_code is not None:
        validate_postal_code(schema.postal_code)

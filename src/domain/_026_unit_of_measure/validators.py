"""
Unit of Measure validators.
"""
from decimal import Decimal
from shared.errors import ValidationError


def validate_code_unique(value: str) -> str:
    """Validate UOM code format and uniqueness.

    Args:
        value: The UOM code string.
    Returns:
        The validated code (uppercased).
    Raises:
        ValidationError: If code format is invalid.
    """
    if not value or not value.strip():
        raise ValidationError("Code cannot be empty.", field="code")
    return value.strip().upper()


def validate_factor_positive(value: Decimal) -> Decimal:
    """Validate that the conversion factor is positive.

    Args:
        value: The conversion factor.
    Returns:
        The validated factor.
    Raises:
        ValidationError: If factor <= 0.
    """
    if value <= Decimal('0'):
        raise ValidationError("Factor must be greater than zero.", field="factor")
    return value


async def validate_no_self_reference(from_uom_id: int, to_uom_id: int) -> None:
    """Validate that from and to UOM are not the same.

    Args:
        from_uom_id: Source unit ID.
        to_uom_id: Target unit ID.
    Raises:
        ValidationError: If from_uom_id == to_uom_id.
    """
    if from_uom_id == to_uom_id:
        raise ValidationError("Cannot convert a unit to itself.")

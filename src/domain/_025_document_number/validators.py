"""
Validation logic for Document Number Generator.
"""
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, ValidationError
from src.domain._025_document_number.models import DocumentSequence


async def validate_unique_prefix(db: AsyncSession, prefix: str) -> None:
    """
    Validate that the given prefix does not already exist.

    Args:
        db: The async database session.
        prefix: The prefix to check.

    Raises:
        DuplicateError: If a sequence with the given prefix already exists.
    """
    stmt = select(DocumentSequence).where(DocumentSequence.prefix == prefix)
    result = await db.execute(stmt)
    if result.scalars().first() is not None:
        raise DuplicateError("DocumentSequence", prefix)


def validate_pattern(pattern: str) -> None:
    """
    Validate that the pattern contains the required placeholders.

    Args:
        pattern: The pattern string.

    Raises:
        ValidationError: If the pattern is invalid.
    """
    if not pattern:
        raise ValidationError("Pattern cannot be empty.", field="pattern")

    # Check for basic required parts, e.g., it must have {seq} or similar if we wanted strictness.
    # At least {prefix} and some form of sequence is expected, but we allow flexibility.
    # A simple validation:
    if "{seq" not in pattern:
        raise ValidationError("Pattern must contain a sequence placeholder like '{seq:04d}'.", field="pattern")

def validate_prefix_format(prefix: str) -> None:
    """
    Validate the prefix format (e.g. alphanumeric only).
    """
    if not prefix:
        raise ValidationError("Prefix cannot be empty.", field="prefix")

    if not re.match(r"^[A-Za-z0-9_-]+$", prefix):
        raise ValidationError(
            "Prefix can only contain alphanumeric characters, underscores, and hyphens.",
            field="prefix"
        )

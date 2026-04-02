"""
Tests for Document Number Generator validators.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError
from shared.errors import ValidationError as AppValidationError
from src.domain._025_document_number.models import DocumentSequence
from src.domain._025_document_number.validators import (
    validate_pattern,
    validate_prefix_format,
    validate_unique_prefix,
)


@pytest.mark.asyncio
async def test_validate_unique_prefix(db: AsyncSession) -> None:
    """Test unique prefix validation."""
    seq = DocumentSequence(prefix="UNIQUE", pattern="{prefix}-{seq}")
    db.add(seq)
    await db.commit()

    # Should raise DuplicateError
    with pytest.raises(DuplicateError):
        await validate_unique_prefix(db, "UNIQUE")

    # Should pass
    await validate_unique_prefix(db, "NEW")


def test_validate_pattern() -> None:
    """Test pattern validation."""
    # Valid
    validate_pattern("{prefix}-{seq:04d}")

    # Invalid
    with pytest.raises(AppValidationError):
        validate_pattern("")
    with pytest.raises(AppValidationError):
        validate_pattern("{prefix}-YYYY")


def test_validate_prefix_format() -> None:
    """Test prefix format validation."""
    # Valid
    validate_prefix_format("PO")
    validate_prefix_format("PO-01")
    validate_prefix_format("PO_01")

    # Invalid
    with pytest.raises(AppValidationError):
        validate_prefix_format("")
    with pytest.raises(AppValidationError):
        validate_prefix_format("PO 01")
    with pytest.raises(AppValidationError):
        validate_prefix_format("PO@01")

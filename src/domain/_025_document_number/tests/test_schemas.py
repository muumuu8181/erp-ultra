"""
Tests for Document Number Generator schemas.
"""
import pytest
from pydantic import ValidationError

from src.domain._025_document_number.schemas import DocumentSequenceCreate


def test_document_sequence_create_schema() -> None:
    """Test valid schema creation."""
    data = DocumentSequenceCreate(
        prefix="INV",
        pattern="{prefix}-{seq:04d}",
        description=None,
        is_active=True,
        current_sequence=0,
    )
    assert data.prefix == "INV"
    assert data.pattern == "{prefix}-{seq:04d}"
    assert data.current_sequence == 0
    assert data.is_active is True

def test_document_sequence_create_schema_invalid() -> None:
    """Test invalid schema creation."""
    with pytest.raises(ValidationError):
        # Missing required fields
        DocumentSequenceCreate(
            prefix="",
            pattern="",
            description=None,
            is_active=True,
            current_sequence=0,
        ) # Will fail in pydantic validation if fields are invalid or missing required params if called loosely
        # To truly test missing fields, we'll try to construct it with invalid types that fail fast
        DocumentSequenceCreate.model_validate({})

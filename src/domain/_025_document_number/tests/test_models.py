"""
Tests for Document Number Generator models.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain._025_document_number.models import DocumentSequence


@pytest.mark.asyncio
async def test_document_sequence_model(db: AsyncSession) -> None:
    """Test creating and retrieving a DocumentSequence model."""
    seq = DocumentSequence(
        prefix="TEST",
        pattern="{prefix}-{seq:04d}",
        description="Test description"
    )
    db.add(seq)
    await db.commit()
    await db.refresh(seq)

    assert seq.id is not None
    assert seq.prefix == "TEST"
    assert seq.pattern == "{prefix}-{seq:04d}"
    assert seq.current_sequence == 0
    assert seq.description == "Test description"
    assert seq.is_active is True
    assert seq.created_at is not None
    assert seq.updated_at is not None

    stmt = select(DocumentSequence).where(DocumentSequence.prefix == "TEST")
    result = await db.execute(stmt)
    fetched = result.scalars().first()
    assert fetched is not None
    assert fetched.id == seq.id

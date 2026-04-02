"""
Tests for Document Number Generator service.
"""
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import BusinessRuleError, NotFoundError
from src.domain._025_document_number.schemas import (
    DocumentSequenceCreate,
    DocumentSequenceUpdate,
)
from src.domain._025_document_number.service import DocumentSequenceService


@pytest.fixture
def service() -> DocumentSequenceService:
    return DocumentSequenceService()


@pytest.mark.asyncio
async def test_crud_service(db: AsyncSession, service: DocumentSequenceService) -> None:
    """Test CRUD operations in service."""
    # Create
    create_data = DocumentSequenceCreate(
        prefix="SO",
        pattern="{prefix}-{YYYY}-{seq:04d}",
        description="Sales Order",
        is_active=True,
        current_sequence=0,
    )
    seq = await service.create(db, create_data, "test_user")
    assert seq.id is not None
    assert seq.prefix == "SO"

    # Get
    fetched = await service.get(db, seq.id)
    assert fetched.prefix == "SO"

    # Get by prefix
    fetched_by_prefix = await service.get_by_prefix(db, "SO")
    assert fetched_by_prefix.id == seq.id

    # List
    items, total = await service.list(db)
    assert total >= 1
    assert any(item.id == seq.id for item in items)

    # Update
    update_data = DocumentSequenceUpdate(pattern=None, description="Updated Sales Order", is_active=False)
    updated = await service.update(db, seq.id, update_data, "test_user2")
    assert updated.description == "Updated Sales Order"
    assert updated.is_active is False

    # Delete
    await service.delete(db, seq.id)
    with pytest.raises(NotFoundError):
        await service.get(db, seq.id)


@pytest.mark.asyncio
async def test_generate_next_number(db: AsyncSession, service: DocumentSequenceService) -> None:
    """Test generating document numbers."""
    create_data = DocumentSequenceCreate(
        prefix="PO",
        pattern="{prefix}-{YYYY}{MM}-{seq:04d}",
        description=None,
        is_active=True,
        current_sequence=0,
    )
    seq = await service.create(db, create_data, "test_user")

    response1 = await service.generate_next_number(db, "PO")
    assert response1.prefix == "PO"
    assert response1.sequence == 1

    today = date.today()
    expected_doc1 = f"PO-{today.strftime('%Y%m')}-0001"
    assert response1.document_number == expected_doc1

    response2 = await service.generate_next_number(db, "PO")
    assert response2.sequence == 2
    expected_doc2 = f"PO-{today.strftime('%Y%m')}-0002"
    assert response2.document_number == expected_doc2

    # Inactive sequence
    await service.update(db, seq.id, DocumentSequenceUpdate(pattern=None, description=None, is_active=False), "test_user")
    with pytest.raises(BusinessRuleError):
        await service.generate_next_number(db, "PO")

    # Not found
    with pytest.raises(NotFoundError):
        await service.generate_next_number(db, "NONEXISTENT")

"""
Tests for Payment Terms service layer.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError

from shared.errors import NotFoundError, DuplicateError, ValidationError
from src.domain._029_payment_terms.models import PaymentTerm
from src.domain._029_payment_terms.schemas import PaymentTermCreate, PaymentTermUpdate
from src.domain._029_payment_terms.service import (
    get_payment_term,
    list_payment_terms,
    create_payment_term,
    update_payment_term,
    delete_payment_term
)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_payment_term_found(mock_db):
    term = PaymentTerm(id=1, code="NET30", name="Net 30")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = term
    mock_db.execute.return_value = mock_result

    result = await get_payment_term(mock_db, 1)
    assert result.id == 1
    assert result.code == "NET30"


@pytest.mark.asyncio
async def test_get_payment_term_not_found(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(NotFoundError):
        await get_payment_term(mock_db, 999)


@pytest.mark.asyncio
async def test_create_payment_term_success(mock_db):
    data = PaymentTermCreate(code="NET30", name="Net 30", days=30)

    # Mock no existing duplicate
    mock_existing = MagicMock()
    mock_existing.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_existing

    # Mock refresh sets an ID
    async def mock_refresh(obj):
        obj.id = 1
    mock_db.refresh.side_effect = mock_refresh

    result = await create_payment_term(mock_db, data)
    assert result.id == 1
    assert result.code == "NET30"
    assert result.days == 30
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_payment_term_duplicate(mock_db):
    data = PaymentTermCreate(code="NET30", name="Net 30", days=30)

    # Mock existing duplicate found
    existing_term = PaymentTerm(id=1, code="NET30", name="Net 30 Old")
    mock_existing = MagicMock()
    mock_existing.scalar_one_or_none.return_value = existing_term
    mock_db.execute.return_value = mock_existing

    with pytest.raises(DuplicateError):
        await create_payment_term(mock_db, data)


@pytest.mark.asyncio
async def test_update_payment_term_success(mock_db):
    term = PaymentTerm(id=1, code="NET30", name="Net 30", days=30)

    # For get_payment_term (finding the original)
    mock_get_result = MagicMock()
    mock_get_result.scalar_one_or_none.return_value = term

    # For duplicate check (finding none)
    mock_dup_result = MagicMock()
    mock_dup_result.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [mock_get_result, mock_dup_result]

    data = PaymentTermUpdate(name="Net 30 Updated", days=35)

    result = await update_payment_term(mock_db, 1, data)
    assert result.name == "Net 30 Updated"
    assert result.days == 35
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_payment_term_success(mock_db):
    term = PaymentTerm(id=1, code="NET30", name="Net 30", days=30)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = term
    mock_db.execute.return_value = mock_result

    result = await delete_payment_term(mock_db, 1)
    assert result is True
    mock_db.delete.assert_called_once_with(term)
    mock_db.commit.assert_called_once()

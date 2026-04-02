from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, ValidationError
from src.inventory._064_inventory_report.schemas import InventoryReportCreate
from src.inventory._064_inventory_report.validators import (
    validate_inventory_report_create,
    validate_report_type,
    validate_status,
    validate_unique_code,
)


@pytest.mark.asyncio
async def test_validate_unique_code_success() -> None:
    db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    db.execute.return_value = mock_result

    await validate_unique_code(db, "NEW-CODE")

@pytest.mark.asyncio
async def test_validate_unique_code_duplicate() -> None:
    db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = MagicMock()
    db.execute.return_value = mock_result

    with pytest.raises(DuplicateError):
        await validate_unique_code(db, "EXISTING-CODE")

def test_validate_report_type() -> None:
    validate_report_type("stock_level")
    with pytest.raises(ValidationError):
        validate_report_type("invalid_type")

def test_validate_status() -> None:
    validate_status("draft")
    with pytest.raises(ValidationError):
        validate_status("invalid_status")

@pytest.mark.asyncio
async def test_validate_create() -> None:
    db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    db.execute.return_value = mock_result

    data = InventoryReportCreate(
        code="REP-001",
        name="Test",
        report_type="stock_level",
        status="draft"
    )

    await validate_inventory_report_create(db, data)

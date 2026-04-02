from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError
from src.inventory._064_inventory_report.models import InventoryReport
from src.inventory._064_inventory_report.schemas import InventoryReportCreate, InventoryReportUpdate
from src.inventory._064_inventory_report.service import (
    create_inventory_report,
    delete_inventory_report,
    get_inventory_report,
    update_inventory_report,
)


from typing import Any

@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)

@pytest.mark.asyncio
async def test_get_inventory_report_success(mock_db: AsyncMock) -> None:
    mock_report = InventoryReport(id=1, code="REP-01")
    mock_db.get.return_value = mock_report

    report = await get_inventory_report(mock_db, 1)
    assert report.id == 1
    assert report.code == "REP-01"

@pytest.mark.asyncio
async def test_get_inventory_report_not_found(mock_db: AsyncMock) -> None:
    mock_db.get.return_value = None
    with pytest.raises(NotFoundError):
        await get_inventory_report(mock_db, 999)

@pytest.mark.asyncio
@patch("src.inventory._064_inventory_report.service.validate_inventory_report_create")
async def test_create_inventory_report(mock_validate: Any, mock_db: AsyncMock) -> None:
    data = InventoryReportCreate(code="REP-01", name="Test", report_type="stock_level")

    report = await create_inventory_report(mock_db, data)

    mock_validate.assert_called_once_with(mock_db, data)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert report.code == "REP-01"

@pytest.mark.asyncio
@patch("src.inventory._064_inventory_report.service.get_inventory_report")
@patch("src.inventory._064_inventory_report.service.validate_inventory_report_update")
async def test_update_inventory_report(mock_validate: Any, mock_get: Any, mock_db: AsyncMock) -> None:
    mock_report = InventoryReport(id=1, code="REP-01", name="Old")
    mock_get.return_value = mock_report

    data = InventoryReportUpdate(name="New")
    report = await update_inventory_report(mock_db, 1, data)

    mock_validate.assert_called_once_with(mock_db, 1, data)
    assert report.name == "New"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
@patch("src.inventory._064_inventory_report.service.get_inventory_report")
async def test_delete_inventory_report(mock_get: Any, mock_db: AsyncMock) -> None:
    mock_report = InventoryReport(id=1, code="REP-01")
    mock_get.return_value = mock_report

    await delete_inventory_report(mock_db, 1)

    mock_db.delete.assert_called_once_with(mock_report)
    mock_db.commit.assert_called_once()

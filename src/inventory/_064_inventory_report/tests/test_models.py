
import pytest

from src.inventory._064_inventory_report.models import InventoryReport


@pytest.mark.asyncio
async def test_inventory_report_model_creation() -> None:
    report = InventoryReport(
        code="REP-001",
        name="Monthly Stock Level",
        report_type="stock_level",
        status="draft"
    )

    assert report.code == "REP-001"
    assert report.name == "Monthly Stock Level"
    assert report.report_type == "stock_level"
    assert report.status == "draft"
    assert report.description is None
    assert report.parameters is None

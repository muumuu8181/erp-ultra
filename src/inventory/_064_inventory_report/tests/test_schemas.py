import pytest
from pydantic import ValidationError

from src.inventory._064_inventory_report.schemas import InventoryReportCreate, InventoryReportUpdate


from typing import Any

def test_inventory_report_create_valid() -> None:
    data: dict[str, Any] = {
        "code": "REP-001",
        "name": "Report 1",
        "report_type": "stock_level",
        "status": "draft"
    }
    schema = InventoryReportCreate(**data)
    assert schema.code == "REP-001"
    assert schema.name == "Report 1"
    assert schema.report_type == "stock_level"

def test_inventory_report_create_missing_fields() -> None:
    data: dict[str, Any] = {"code": "REP-001"}
    with pytest.raises(ValidationError):
        InventoryReportCreate(**data)

def test_inventory_report_update_valid() -> None:
    data: dict[str, Any] = {"name": "New Name", "status": "completed"}
    schema = InventoryReportUpdate(**data)
    assert schema.name == "New Name"
    assert schema.status == "completed"
    assert schema.code is None

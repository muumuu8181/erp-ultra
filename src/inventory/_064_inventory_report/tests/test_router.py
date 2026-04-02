from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.foundation._001_database.engine import get_db
from src.inventory._064_inventory_report.router import router
from src.inventory._064_inventory_report.schemas import InventoryReportResponse

app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Dependency override
from typing import Any, AsyncGenerator

async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
    yield AsyncMock()

app.dependency_overrides[get_db] = override_get_db

@patch("src.inventory._064_inventory_report.service.create_inventory_report")
def test_create_report_route(mock_create: Any) -> None:
    mock_create.return_value = InventoryReportResponse(
        id=1,
        code="REP-001",
        name="Test Report",
        report_type="stock_level",
        status="draft",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    response = client.post("/api/v1/inventory-reports/", json={
        "code": "REP-001",
        "name": "Test Report",
        "report_type": "stock_level"
    })

    assert response.status_code == 201
    assert response.json()["code"] == "REP-001"

@patch("src.inventory._064_inventory_report.service.get_inventory_report")
def test_get_report_route(mock_get: Any) -> None:
    mock_get.return_value = InventoryReportResponse(
        id=1,
        code="REP-001",
        name="Test Report",
        report_type="stock_level",
        status="draft",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    response = client.get("/api/v1/inventory-reports/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

@patch("src.inventory._064_inventory_report.service.delete_inventory_report")
def test_delete_report_route(mock_delete: Any) -> None:
    mock_delete.return_value = None
    response = client.delete("/api/v1/inventory-reports/1")
    assert response.status_code == 204

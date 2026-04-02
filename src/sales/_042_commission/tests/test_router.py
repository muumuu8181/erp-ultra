import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from sales._042_commission.router import router
from fastapi import FastAPI
from foundation._001_database import get_db

app = FastAPI()
app.include_router(router)

async def override_get_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

MOCK_COMMISSION = {
    "id": 1,
    "salesperson_id": 1,
    "sales_order_id": 2,
    "commission_rate": "10.5",
    "amount": "100.00",
    "currency": "JPY",
    "status": "active",
    "calculation_date": "2023-01-01",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
}

@patch("sales._042_commission.service.create_commission")
def test_create_commission_endpoint(mock_create):
    mock_create.return_value = MOCK_COMMISSION

    response = client.post(
        "/api/v1/sales-commission/",
        json={
            "salesperson_id": 1,
            "sales_order_id": 2,
            "commission_rate": "10.5",
            "amount": "100.00",
            "calculation_date": "2023-01-01"
        }
    )
    assert response.status_code == 201
    assert response.json()["id"] == 1

@patch("sales._042_commission.service.get_commission")
def test_get_commission_endpoint(mock_get):
    mock_get.return_value = MOCK_COMMISSION
    response = client.get("/api/v1/sales-commission/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

@patch("sales._042_commission.service.update_commission")
def test_update_commission_endpoint(mock_update):
    mock_update.return_value = MOCK_COMMISSION
    response = client.put(
        "/api/v1/sales-commission/1",
        json={"amount": "200.00"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == 1

@patch("sales._042_commission.service.delete_commission")
def test_delete_commission_endpoint(mock_delete):
    response = client.delete("/api/v1/sales-commission/1")
    assert response.status_code == 204

@patch("sales._042_commission.service.list_commissions")
def test_list_commissions_endpoint(mock_list):
    mock_list.return_value = ([MOCK_COMMISSION], 1)
    response = client.get("/api/v1/sales-commission/")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1

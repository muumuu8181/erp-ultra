import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from fastapi import FastAPI

# To test the router we need to mount it to an app
from src.inventory._061_inventory_valuation.router import router

pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(router)
    return app

# Testing router requires httpx AsyncClient in true integration test.
# But we can test endpoints status code via httpx AsyncClient.

from httpx import AsyncClient, ASGITransport

async def test_create_valuation_method(test_app, db_session):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/inventory-valuation/valuation-methods", json={
            "product_code": "API-PROD-01",
            "method": "fifo",
            "effective_from": str(date.today())
        })
    assert response.status_code == 201
    data = response.json()
    assert data["product_code"] == "API-PROD-01"

async def test_create_cost_layer(test_app, db_session):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/inventory-valuation/cost-layers", json={
            "product_code": "API-PROD-01",
            "warehouse_code": "WH-01",
            "received_date": str(date.today()),
            "quantity": "100.0",
            "unit_cost": "15.0"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["remaining_quantity"] == "100.0"

async def test_calculate_valuation_endpoint(test_app, db_session):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        await ac.post("/api/v1/inventory-valuation/valuation-methods", json={
            "product_code": "API-PROD-02", "method": "fifo", "effective_from": str(date.today())
        })
        await ac.post("/api/v1/inventory-valuation/cost-layers", json={
            "product_code": "API-PROD-02", "warehouse_code": "WH-01",
            "received_date": str(date.today()), "quantity": "10.0", "unit_cost": "10.0"
        })
        response = await ac.post("/api/v1/inventory-valuation/calculate", json={
            "product_code": "API-PROD-02"
        })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert Decimal(data[0]["total_value"]) == Decimal("100.0")

async def test_get_report_and_summary(test_app, db_session):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        report_response = await ac.get("/api/v1/inventory-valuation/report?product_code=API-PROD-02")
        assert report_response.status_code == 200
        assert "total_value" in report_response.json()

        summary_response = await ac.get("/api/v1/inventory-valuation/summary")
        assert summary_response.status_code == 200
        assert "total_items" in summary_response.json()

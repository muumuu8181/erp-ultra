import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from src.inventory._061_inventory_valuation.router import router

pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(router)
    return app

async def test_consume_cost_layer_endpoint(test_app, db_session):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        await ac.post("/api/v1/inventory-valuation/valuation-methods", json={
            "product_code": "CONSUME-PROD", "method": "fifo", "effective_from": str(date.today())
        })
        await ac.post("/api/v1/inventory-valuation/cost-layers", json={
            "product_code": "CONSUME-PROD", "warehouse_code": "WH-01",
            "received_date": str(date.today()), "quantity": "100.0", "unit_cost": "10.0"
        })

        response = await ac.post("/api/v1/inventory-valuation/cost-layers/consume", json={
            "product_code": "CONSUME-PROD",
            "warehouse_code": "WH-01",
            "quantity": "20.0"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert Decimal(data[0]["remaining_quantity"]) == Decimal("80.0")

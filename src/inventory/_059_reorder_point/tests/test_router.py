import pytest
from httpx import AsyncClient
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from src.inventory._059_reorder_point.models import ReorderPoint, ReorderAlert
from src.inventory._059_reorder_point.schemas import ReviewCycleEnum, AlertStatusEnum

pytestmark = pytest.mark.asyncio


async def test_create_reorder_point_router(client: AsyncClient):
    payload = {
        "product_code": "API-PROD-1",
        "warehouse_code": "API-WH-1",
        "reorder_point": "100.000",
        "safety_stock": "20.000",
        "reorder_quantity": "50.000",
        "lead_time_days": 7,
        "review_cycle": "daily",
        "is_active": True
    }

    response = await client.post("/api/v1/reorder-point/reorder-points", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["product_code"] == "API-PROD-1"
    assert "id" in data


async def test_get_reorder_point_router(client: AsyncClient, db: AsyncSession):
    payload = {
        "product_code": "API-PROD-GET",
        "warehouse_code": "API-WH-GET",
        "reorder_point": "100.000",
        "safety_stock": "20.000",
        "reorder_quantity": "50.000",
        "lead_time_days": 7,
        "review_cycle": "daily"
    }
    create_res = await client.post("/api/v1/reorder-point/reorder-points", json=payload)
    rp_id = create_res.json()["id"]

    response = await client.get(f"/api/v1/reorder-point/reorder-points/{rp_id}")
    assert response.status_code == 200
    assert response.json()["product_code"] == "API-PROD-GET"

    response_404 = await client.get("/api/v1/reorder-point/reorder-points/9999")
    assert response_404.status_code == 404


async def test_delete_reorder_point_router(client: AsyncClient, db: AsyncSession):
    payload = {
        "product_code": "API-PROD-DEL",
        "warehouse_code": "API-WH-DEL",
        "reorder_point": "100.000",
        "safety_stock": "20.000",
        "reorder_quantity": "50.000",
        "lead_time_days": 7,
        "review_cycle": "daily"
    }
    create_res = await client.post("/api/v1/reorder-point/reorder-points", json=payload)
    rp_id = create_res.json()["id"]

    response = await client.delete(f"/api/v1/reorder-point/reorder-points/{rp_id}")
    assert response.status_code == 204

    response_get = await client.get(f"/api/v1/reorder-point/reorder-points/{rp_id}")
    assert response_get.status_code == 404


async def test_create_reorder_point_validation_error(client: AsyncClient):
    payload = {
        "product_code": "API-PROD-2",
        "warehouse_code": "API-WH-1",
        "reorder_point": "10.000",
        "safety_stock": "20.000", # Error: reorder_point < safety_stock
        "reorder_quantity": "50.000",
        "lead_time_days": 7,
        "review_cycle": "daily"
    }

    response = await client.post("/api/v1/reorder-point/reorder-points", json=payload)
    assert response.status_code == 422


async def test_list_reorder_points_router(client: AsyncClient, db: AsyncSession):
    # Already created one in previous test, let's create another
    payload = {
        "product_code": "API-PROD-3",
        "warehouse_code": "API-WH-2",
        "reorder_point": "100.000",
        "safety_stock": "20.000",
        "reorder_quantity": "50.000",
        "lead_time_days": 7,
        "review_cycle": "daily"
    }
    await client.post("/api/v1/reorder-point/reorder-points", json=payload)

    response = await client.get("/api/v1/reorder-point/reorder-points?warehouse_code=API-WH-2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["warehouse_code"] == "API-WH-2"


@patch('src.inventory._059_reorder_point.service._get_current_stock_stub', return_value=Decimal("10"))
async def test_check_reorder_points_router(mock_stock, client: AsyncClient):
    response = await client.post("/api/v1/reorder-point/reorder-points/check")
    assert response.status_code == 200
    # Should generate alerts for all existing active ones because stub returns 10 < 100
    data = response.json()
    assert isinstance(data, list)


async def test_resolve_alert_router(client: AsyncClient, db: AsyncSession):
    # Setup an alert manually
    alert = ReorderAlert(
        product_code="API-PROD-9",
        warehouse_code="API-WH-9",
        current_stock=Decimal("10"),
        reorder_point=Decimal("50"),
        deficit=Decimal("40"),
        status=AlertStatusEnum.PENDING.value
    )
    db.add(alert)
    await db.flush()
    alert_id = alert.id
    await db.commit()

    response = await client.post(f"/api/v1/reorder-point/reorder-alerts/{alert_id}/resolve")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"


async def test_calculate_safety_stock_router(client: AsyncClient, db: AsyncSession):
    # create point
    payload = {
        "product_code": "API-PROD-SS",
        "warehouse_code": "API-WH-1",
        "reorder_point": "100.000",
        "safety_stock": "20.000",
        "reorder_quantity": "50.000",
        "lead_time_days": 7,
        "review_cycle": "daily"
    }
    create_res = await client.post("/api/v1/reorder-point/reorder-points", json=payload)
    rp_id = create_res.json()["id"]

    response = await client.post(f"/api/v1/reorder-point/reorder-points/{rp_id}/safety-stock?demand_std_dev=10&lead_time_days=7")
    assert response.status_code == 200
    # response is just a float/string of Decimal
    assert float(response.text) == 43.655


async def test_suggest_quantity_router(client: AsyncClient, db: AsyncSession):
    # create point
    payload = {
        "product_code": "API-PROD-SG",
        "warehouse_code": "API-WH-1",
        "reorder_point": "100.000",
        "safety_stock": "20.000",
        "reorder_quantity": "50.000",
        "lead_time_days": 7,
        "review_cycle": "daily"
    }
    create_res = await client.post("/api/v1/reorder-point/reorder-points", json=payload)
    rp_id = create_res.json()["id"]

    response = await client.post(
        f"/api/v1/reorder-point/reorder-points/{rp_id}/suggest-quantity?annual_demand=1000&ordering_cost=10&holding_cost_pct=2"
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["suggested_quantity"]) == 100.0
    assert "EOQ" in data["rationale"]

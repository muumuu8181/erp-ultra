import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from src.inventory._060_stock_alert.router import router
from src.foundation._001_database.engine import get_db

app = FastAPI()
app.include_router(router)


@pytest_asyncio.fixture
async def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_post_alert_rules_201(client: AsyncClient):
    data = {
        "name": "Router Test Rule",
        "alert_type": "low_stock",
        "product_code": "PROD-1",
        "threshold_value": 10.5,
        "threshold_operator": "less_than",
        "comparison_field": "quantity",
        "notify_users": ["router@test.com"]
    }
    response = await client.post("/api/v1/stock-alert/alert-rules", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Router Test Rule"
    assert "id" in result


@pytest.mark.asyncio
async def test_invalid_data_422(client: AsyncClient):
    data = {
        "name": "Invalid Rule",
        "alert_type": "low_stock",
        "threshold_value": -5.0,  # invalid
        "threshold_operator": "less_than",
        "comparison_field": "quantity",
        "notify_users": []  # invalid
    }
    response = await client.post("/api/v1/stock-alert/alert-rules", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_evaluate(client: AsyncClient):
    # Setup rule via API
    data = {
        "name": "Eval Rule",
        "alert_type": "high_stock",
        "warehouse_code": "WH-EVAL",
        "threshold_value": 10.0,
        "threshold_operator": "greater_than", # should be less than 50 random
        "comparison_field": "quantity",
        "notify_users": ["eval@test.com"]
    }
    await client.post("/api/v1/stock-alert/alert-rules", json=data)

    response = await client.post("/api/v1/stock-alert/stock-alerts/evaluate?warehouse_code=WH-EVAL")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_post_acknowledge(client: AsyncClient):
    # First evaluate to get an alert
    data = {
        "name": "Ack Rule",
        "alert_type": "high_stock",
        "threshold_value": 0.0,
        "threshold_operator": "greater_than",
        "comparison_field": "quantity",
        "notify_users": ["ack@test.com"]
    }
    await client.post("/api/v1/stock-alert/alert-rules", json=data)
    eval_resp = await client.post("/api/v1/stock-alert/stock-alerts/evaluate")
    alerts = eval_resp.json()
    assert len(alerts) > 0
    alert_id = alerts[0]["id"]

    response = await client.post(
        f"/api/v1/stock-alert/stock-alerts/{alert_id}/acknowledge",
        json={"acknowledged_by": "test_user"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_endpoints_status_codes(client: AsyncClient):
    # list rules
    resp = await client.get("/api/v1/stock-alert/alert-rules")
    assert resp.status_code == 200

    # list alerts
    resp = await client.get("/api/v1/stock-alert/stock-alerts")
    assert resp.status_code == 200
    assert "items" in resp.json()

    # get stats
    resp = await client.get("/api/v1/stock-alert/stock-alerts/stats")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_cleanup(client: AsyncClient):
    resp = await client.delete("/api/v1/stock-alert/stock-alerts/cleanup?days=90")
    assert resp.status_code == 200
    assert "deleted_count" in resp.json()

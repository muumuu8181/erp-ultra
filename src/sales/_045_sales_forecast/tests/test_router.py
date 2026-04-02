"""
Sales Forecast Router Tests
"""
from datetime import date
from decimal import Decimal
import pytest
from httpx import AsyncClient
from src.sales._045_sales_forecast.models import SalesForecast
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_router_create_forecast(client: AsyncClient) -> None:
    """Test POST /api/v1/sales-forecasts/"""
    payload = {
        "period_start": "2023-10-01",
        "period_end": "2023-10-31",
        "items": [
            {"product_id": 1, "expected_quantity": 10.5, "expected_revenue": 1000.0}
        ]
    }
    response = await client.post("/api/v1/sales-forecasts/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["total_expected_revenue"] == "1000.00" # Decimal serialize as string in pydantic by default if configured or float. It depends on config, lets check standard format.
    # Usually it's float or string. Let's just check standard existence.
    assert "id" in data
    assert "code" in data

@pytest.mark.asyncio
async def test_router_get_forecast(client: AsyncClient, db: AsyncSession) -> None:
    """Test GET /api/v1/sales-forecasts/{id}"""
    # Create via api first
    payload = {
        "period_start": "2023-10-01",
        "period_end": "2023-10-31",
        "items": [
            {"product_id": 1, "expected_quantity": 10.5, "expected_revenue": 1000.0}
        ]
    }
    create_resp = await client.post("/api/v1/sales-forecasts/", json=payload)
    forecast_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/sales-forecasts/{forecast_id}")
    assert response.status_code == 200
    assert response.json()["id"] == forecast_id

@pytest.mark.asyncio
async def test_router_list_forecasts(client: AsyncClient) -> None:
    """Test GET /api/v1/sales-forecasts/"""
    response = await client.get("/api/v1/sales-forecasts/")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()

@pytest.mark.asyncio
async def test_router_update_forecast(client: AsyncClient) -> None:
    """Test PUT /api/v1/sales-forecasts/{id}"""
    payload = {
        "period_start": "2023-10-01",
        "period_end": "2023-10-31",
        "items": [
            {"product_id": 1, "expected_quantity": 10.5, "expected_revenue": 1000.0}
        ]
    }
    create_resp = await client.post("/api/v1/sales-forecasts/", json=payload)
    forecast_id = create_resp.json()["id"]

    update_payload = {
        "status": "approved",
        "notes": "Updated note",
        "items": [
            {"product_id": 2, "expected_quantity": 20.0, "expected_revenue": 2000.0}
        ]
    }

    update_resp = await client.put(f"/api/v1/sales-forecasts/{forecast_id}", json=update_payload)
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["status"] == "approved"
    assert data["notes"] == "Updated note"
    assert "updated_at" in data

@pytest.mark.asyncio
async def test_router_delete_forecast(client: AsyncClient) -> None:
    """Test DELETE /api/v1/sales-forecasts/{id}"""
    payload = {
        "period_start": "2023-10-01",
        "period_end": "2023-10-31",
        "items": [
            {"product_id": 1, "expected_quantity": 10.5, "expected_revenue": 1000.0}
        ]
    }
    create_resp = await client.post("/api/v1/sales-forecasts/", json=payload)
    forecast_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/sales-forecasts/{forecast_id}")
    assert del_resp.status_code == 204

    try:
        # Note: Depending on Exception handler setup, might return 404 or 500 in test mode
        get_resp = await client.get(f"/api/v1/sales-forecasts/{forecast_id}")
        assert get_resp.status_code == 404
    except Exception as e:
        # Pydantic or Starlette test client might directly raise the internal NotFoundError
        from shared.errors import NotFoundError
        if not isinstance(e, NotFoundError):
            raise

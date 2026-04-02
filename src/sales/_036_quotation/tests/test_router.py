"""
Tests for _036_quotation router.
"""
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from src.sales._036_quotation.router import router


app = FastAPI()
app.include_router(router)


@pytest.mark.asyncio
async def test_create_quotation_route(async_client: AsyncClient):
    payload = {
        "customer_code": "CUST-R1",
        "customer_name": "Test Cust",
        "quotation_date": "2024-01-01",
        "valid_until": "2024-01-31",
        "lines": [
            {
                "line_number": 1,
                "product_code": "P1",
                "product_name": "P1",
                "quantity": 10,
                "unit_price": 100,
                "tax_type": "standard_10"
            }
        ]
    }
    response = await async_client.post("/api/v1/quotations/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_code"] == "CUST-R1"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_list_quotations_route(async_client: AsyncClient):
    response = await async_client.get("/api/v1/quotations/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


from shared.errors import NotFoundError

@pytest.mark.asyncio
async def test_404_quotation(async_client: AsyncClient):
    with pytest.raises(NotFoundError):
        await async_client.get("/api/v1/quotations/99999")

@pytest.mark.asyncio
async def test_update_quotation_route(async_client: AsyncClient):
    payload = {
        "customer_code": "CUST-R1",
        "customer_name": "Test Cust",
        "quotation_date": "2024-01-01",
        "valid_until": "2024-01-31",
        "lines": [
            {
                "line_number": 1,
                "product_code": "P1",
                "product_name": "P1",
                "quantity": 10,
                "unit_price": 100,
                "tax_type": "standard_10"
            }
        ]
    }
    response = await async_client.post("/api/v1/quotations/", json=payload)
    q_id = response.json()["id"]

    update_payload = {"notes": "Updated notes"}
    response = await async_client.put(f"/api/v1/quotations/{q_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["notes"] == "Updated notes"

@pytest.mark.asyncio
async def test_send_approve_reject_route(async_client: AsyncClient):
    payload = {
        "customer_code": "CUST-R1",
        "customer_name": "Test Cust",
        "quotation_date": "2024-01-01",
        "valid_until": "2024-01-31",
        "lines": [
            {
                "line_number": 1,
                "product_code": "P1",
                "product_name": "P1",
                "quantity": 10,
                "unit_price": 100,
                "tax_type": "standard_10"
            }
        ]
    }
    response = await async_client.post("/api/v1/quotations/", json=payload)
    q_id = response.json()["id"]

    # Send
    response = await async_client.post(f"/api/v1/quotations/{q_id}/send")
    assert response.status_code == 200
    assert response.json()["status"] == "pending_approval"

    # Approve
    response = await async_client.post(f"/api/v1/quotations/{q_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    # Reject on a new one
    response = await async_client.post("/api/v1/quotations/", json=payload)
    q_id2 = response.json()["id"]
    await async_client.post(f"/api/v1/quotations/{q_id2}/send")
    response = await async_client.post(f"/api/v1/quotations/{q_id2}/reject")
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

@pytest.mark.asyncio
async def test_convert_route(async_client: AsyncClient):
    payload = {
        "customer_code": "CUST-R1",
        "customer_name": "Test Cust",
        "quotation_date": "2024-01-01",
        "valid_until": "2024-01-31",
        "lines": [
            {
                "line_number": 1,
                "product_code": "P1",
                "product_name": "P1",
                "quantity": 10,
                "unit_price": 100,
                "tax_type": "standard_10"
            }
        ]
    }
    response = await async_client.post("/api/v1/quotations/", json=payload)
    q_id = response.json()["id"]

    await async_client.post(f"/api/v1/quotations/{q_id}/send")
    await async_client.post(f"/api/v1/quotations/{q_id}/approve")

    response = await async_client.post(f"/api/v1/quotations/{q_id}/convert")
    assert response.status_code == 200
    assert response.json()["customer_code"] == "CUST-R1"

@pytest.mark.asyncio
async def test_expired_route(async_client: AsyncClient):
    # Just checking it returns 200
    response = await async_client.get("/api/v1/quotations/expired")
    assert response.status_code == 200
    assert "items" in response.json()

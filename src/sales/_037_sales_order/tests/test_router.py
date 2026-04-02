import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_sales_order_api(client: AsyncClient):
    payload = {
        "customer_id": 1,
        "items": [
            {"product_id": 10, "quantity": "2", "unit_price": "50.00"}
        ]
    }
    response = await client.post("/api/v1/sales-orders/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == 1
    assert data["total_amount"] == "100.00"
    assert len(data["items"]) == 1

@pytest.mark.asyncio
async def test_get_sales_order_api(client: AsyncClient):
    payload = {
        "customer_id": 1,
        "items": [
            {"product_id": 10, "quantity": "2", "unit_price": "50.00"}
        ]
    }
    create_resp = await client.post("/api/v1/sales-orders/", json=payload)
    order_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/sales-orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id

@pytest.mark.asyncio
async def test_list_sales_orders_api(client: AsyncClient):
    payload = {
        "customer_id": 1,
        "items": [
            {"product_id": 10, "quantity": "2", "unit_price": "50.00"}
        ]
    }
    await client.post("/api/v1/sales-orders/", json=payload)

    response = await client.get("/api/v1/sales-orders/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1

@pytest.mark.asyncio
async def test_update_sales_order_status_api(client: AsyncClient):
    payload = {
        "customer_id": 1,
        "items": [
            {"product_id": 10, "quantity": "2", "unit_price": "50.00"}
        ]
    }
    create_resp = await client.post("/api/v1/sales-orders/", json=payload)
    order_id = create_resp.json()["id"]

    update_payload = {"status": "approved"}
    response = await client.patch(f"/api/v1/sales-orders/{order_id}/status", json=update_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

@pytest.mark.asyncio
async def test_delete_sales_order_api(client: AsyncClient):
    payload = {
        "customer_id": 1,
        "items": [
            {"product_id": 10, "quantity": "2", "unit_price": "50.00"}
        ]
    }
    create_resp = await client.post("/api/v1/sales-orders/", json=payload)
    order_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/sales-orders/{order_id}")
    assert response.status_code == 204

    with pytest.raises(Exception):
        await client.get(f"/api/v1/sales-orders/{order_id}")

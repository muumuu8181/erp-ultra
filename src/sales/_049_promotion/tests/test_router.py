import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_promotion_endpoint(client: AsyncClient):
    data = {
        "code": "API-PROMO-1",
        "name": "API Promotion 1",
        "promotion_type": "percentage_off",
        "value": "15.0",
        "product_codes": ["P1", "P2"],
        "customer_groups": [],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "is_active": True
    }
    response = await client.post("/api/v1/promotions", json=data)
    assert response.status_code == 201
    assert response.json()["code"] == "API-PROMO-1"

@pytest.mark.asyncio
async def test_create_promotion_duplicate_code(client: AsyncClient):
    data = {
        "code": "API-PROMO-DUP",
        "name": "API Promotion Dup",
        "promotion_type": "percentage_off",
        "value": "15.0",
        "product_codes": ["P1", "P2"],
        "customer_groups": [],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "is_active": True
    }
    await client.post("/api/v1/promotions", json=data)
    response = await client.post("/api/v1/promotions", json=data)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_list_promotions_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/promotions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_update_promotion_endpoint(client: AsyncClient):
    data = {
        "code": "API-PROMO-UPD",
        "name": "API Promotion Update",
        "promotion_type": "fixed_off",
        "value": "15.0",
        "product_codes": ["P1"],
        "customer_groups": [],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "is_active": True
    }
    create_response = await client.post("/api/v1/promotions", json=data)
    promo_id = create_response.json()["id"]

    update_data = {"name": "Updated Name"}
    response = await client.put(f"/api/v1/promotions/{promo_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

@pytest.mark.asyncio
async def test_evaluate_promotions_endpoint(client: AsyncClient):
    data = {
        "code": "API-PROMO-EVAL",
        "name": "API Promotion Eval",
        "promotion_type": "percentage_off",
        "value": "10.0",
        "product_codes": ["P1"],
        "customer_groups": [],
        "start_date": "2020-01-01", # Ensure it's active based on current date mock if any or real date
        "end_date": "2099-12-31",
        "is_active": True
    }
    await client.post("/api/v1/promotions", json=data)

    eval_data = {
        "cart_items": [
            {
                "product_code": "P1",
                "quantity": "2",
                "unit_price": "100.0"
            }
        ],
        "customer_code": "C1"
    }
    response = await client.post("/api/v1/promotions/evaluate", json=eval_data)
    assert response.status_code == 200
    assert "applicable_promotions" in response.json()

@pytest.mark.asyncio
async def test_redeem_promotion_endpoint(client: AsyncClient):
    data = {
        "code": "API-PROMO-RED",
        "name": "API Promotion Redeem",
        "promotion_type": "fixed_off",
        "value": "10.0",
        "product_codes": ["P1"],
        "customer_groups": [],
        "start_date": "2020-01-01",
        "end_date": "2099-12-31",
        "is_active": True
    }
    create_response = await client.post("/api/v1/promotions", json=data)
    promo_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/promotions/{promo_id}/redeem",
        json={
            "order_number": "ORD-1",
            "customer_code": "C1",
            "redeemed_value": "10.0"
        }
    )
    assert response.status_code == 200
    assert response.json()["promotion_id"] == promo_id

@pytest.mark.asyncio
async def test_get_redemptions_endpoint(client: AsyncClient):
    data = {
        "code": "API-PROMO-RED-LIST",
        "name": "API Promotion Redeem List",
        "promotion_type": "fixed_off",
        "value": "10.0",
        "product_codes": ["P1"],
        "customer_groups": [],
        "start_date": "2020-01-01",
        "end_date": "2099-12-31",
        "is_active": True
    }
    create_response = await client.post("/api/v1/promotions", json=data)
    promo_id = create_response.json()["id"]

    await client.post(
        f"/api/v1/promotions/{promo_id}/redeem",
        json={
            "order_number": "ORD-1",
            "customer_code": "C1",
            "redeemed_value": "10.0"
        }
    )

    response = await client.get(f"/api/v1/promotions/{promo_id}/redemptions")
    assert response.status_code == 200
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_deactivate_promotion_endpoint(client: AsyncClient):
    data = {
        "code": "API-PROMO-DEL",
        "name": "API Promotion Del",
        "promotion_type": "fixed_off",
        "value": "10.0",
        "product_codes": ["P1"],
        "customer_groups": [],
        "start_date": "2020-01-01",
        "end_date": "2099-12-31",
        "is_active": True
    }
    create_response = await client.post("/api/v1/promotions", json=data)
    promo_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/promotions/{promo_id}")
    assert response.status_code == 200
    assert response.json()["is_active"] is False

"""
Tests for Unit of Measure router.
"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_create_uom(async_client):
    response = await async_client.post("/api/v1/uoms", json={
        "code": "TEST_UOM",
        "name": "Test UOM",
        "symbol": "tu",
        "uom_type": "count",
        "decimal_places": 0
    })
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "TEST_UOM"

    # Duplicate code
    response2 = await async_client.post("/api/v1/uoms", json={
        "code": "TEST_UOM",
        "name": "Another UOM",
        "symbol": "au",
        "uom_type": "count",
        "decimal_places": 0
    })
    # Error handling middleware usually converts to 409
    # But since we're assuming the shared.errors handlers are in place, we just expect not 201
    assert response2.status_code in (400, 409)


@pytest.mark.asyncio
async def test_list_uoms(async_client):
    # Setup some data
    await async_client.post("/api/v1/uoms", json={
        "code": "UOM1", "name": "U 1", "symbol": "u1", "uom_type": "count", "decimal_places": 0
    })
    await async_client.post("/api/v1/uoms", json={
        "code": "UOM2", "name": "U 2", "symbol": "u2", "uom_type": "weight", "decimal_places": 0
    })

    response = await async_client.get("/api/v1/uoms")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2

    # Filter
    response = await async_client.get("/api/v1/uoms?uom_type=weight")
    assert response.status_code == 200
    data = response.json()
    assert all(item["uom_type"] == "weight" for item in data["items"])


@pytest.mark.asyncio
async def test_conversions(async_client):
    res1 = await async_client.post("/api/v1/uoms", json={
        "code": "U1", "name": "U 1", "symbol": "u1", "uom_type": "count", "decimal_places": 0
    })
    res2 = await async_client.post("/api/v1/uoms", json={
        "code": "U2", "name": "U 2", "symbol": "u2", "uom_type": "count", "decimal_places": 0
    })
    id1 = res1.json()["id"]
    id2 = res2.json()["id"]

    # Create conversion
    conv_res = await async_client.post("/api/v1/uoms/conversions", json={
        "from_uom_id": id1,
        "to_uom_id": id2,
        "factor": 10.5
    })
    assert conv_res.status_code == 201

    # Self reference
    conv_err = await async_client.post("/api/v1/uoms/conversions", json={
        "from_uom_id": id1,
        "to_uom_id": id1,
        "factor": 10.5
    })
    assert conv_err.status_code in (400, 422)

    # List conversions
    list_res = await async_client.get(f"/api/v1/uoms/conversions?uom_id={id1}")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # Convert quantity
    convert_res = await async_client.post("/api/v1/uoms/convert", json={
        "from_uom_id": id1,
        "to_uom_id": id2,
        "quantity": 2
    })
    assert convert_res.status_code == 200
    assert float(convert_res.json()["converted_quantity"]) == 21.0

    # Get compatible
    compat_res = await async_client.get(f"/api/v1/uoms/{id1}/compatible")
    assert compat_res.status_code == 200
    assert len(compat_res.json()) >= 2

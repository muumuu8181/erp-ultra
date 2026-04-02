import pytest
from httpx import AsyncClient
from src.inventory._056_serial_tracking.models import SerialStatus

@pytest.fixture
def sample_payload():
    return {
        "serial_number": "SN-ROUTER-001",
        "product_code": "PROD-R",
        "warehouse_code": "WH-R"
    }

@pytest.mark.asyncio
async def test_register_serial(client: AsyncClient, sample_payload):
    response = await client.post("/api/v1/serials", json=sample_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["serial_number"] == "SN-ROUTER-001"

@pytest.mark.asyncio
async def test_list_serials(client: AsyncClient, sample_payload):
    await client.post("/api/v1/serials", json=sample_payload)
    response = await client.get("/api/v1/serials")
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_get_serial(client: AsyncClient, sample_payload):
    resp1 = await client.post("/api/v1/serials", json=sample_payload)
    serial_id = resp1.json()["id"]

    response = await client.get(f"/api/v1/serials/{serial_id}")
    assert response.status_code == 200
    assert response.json()["id"] == serial_id

@pytest.mark.asyncio
async def test_reserve_serial(client: AsyncClient, sample_payload):
    resp1 = await client.post("/api/v1/serials", json=sample_payload)
    serial_id = resp1.json()["id"]

    response = await client.post(f"/api/v1/serials/{serial_id}/reserve", json={"reference_type": "ORDER", "reference_number": "ORD-1"})
    assert response.status_code == 200
    assert response.json()["status"] == SerialStatus.reserved.value

@pytest.mark.asyncio
async def test_ship_serial(client: AsyncClient, sample_payload):
    resp1 = await client.post("/api/v1/serials", json=sample_payload)
    serial_id = resp1.json()["id"]

    await client.post(f"/api/v1/serials/{serial_id}/reserve", json={"reference_type": "ORDER", "reference_number": "ORD-1"})

    response = await client.post(f"/api/v1/serials/{serial_id}/ship", json={
        "customer_code": "CUST1",
        "sale_date": "2023-01-01",
        "reference_type": "SHIP",
        "reference_number": "SHP-1"
    })
    assert response.status_code == 200
    assert response.json()["status"] == SerialStatus.shipped.value

@pytest.mark.asyncio
async def test_return_serial(client: AsyncClient, sample_payload):
    resp1 = await client.post("/api/v1/serials", json=sample_payload)
    serial_id = resp1.json()["id"]

    await client.post(f"/api/v1/serials/{serial_id}/reserve", json={"reference_type": "ORDER", "reference_number": "ORD-1"})
    await client.post(f"/api/v1/serials/{serial_id}/ship", json={
        "customer_code": "CUST1",
        "sale_date": "2023-01-01",
        "reference_type": "SHIP",
        "reference_number": "SHP-1"
    })

    response = await client.post(f"/api/v1/serials/{serial_id}/return", json={
        "reason": "Defect",
        "reference_type": "RET",
        "reference_number": "RET-1"
    })
    assert response.status_code == 200
    assert response.json()["status"] == SerialStatus.in_stock.value

@pytest.mark.asyncio
async def test_transfer_serial(client: AsyncClient, sample_payload):
    resp1 = await client.post("/api/v1/serials", json=sample_payload)
    serial_id = resp1.json()["id"]

    response = await client.post(f"/api/v1/serials/{serial_id}/transfer", json={
        "to_warehouse": "WH-NEW",
        "reference_number": "TRF-1"
    })
    assert response.status_code == 200
    assert response.json()["warehouse_code"] == "WH-NEW"

@pytest.mark.asyncio
async def test_scrap_serial(client: AsyncClient, sample_payload):
    resp1 = await client.post("/api/v1/serials", json=sample_payload)
    serial_id = resp1.json()["id"]

    response = await client.post(f"/api/v1/serials/{serial_id}/scrap", json={
        "reason": "Broken",
        "reference_type": "SCRAP",
        "reference_number": "SCR-1"
    })
    assert response.status_code == 200
    assert response.json()["status"] == SerialStatus.scrapped.value

@pytest.mark.asyncio
async def test_trace_serial(client: AsyncClient, sample_payload):
    await client.post("/api/v1/serials", json=sample_payload)

    response = await client.post("/api/v1/serials/trace", json={
        "serial_number": sample_payload["serial_number"],
        "direction": "forward"
    })
    assert response.status_code == 200
    assert len(response.json()["history"]) > 0

@pytest.mark.asyncio
async def test_warranty_check(client: AsyncClient, sample_payload):
    await client.post("/api/v1/serials", json=sample_payload)

    response = await client.post("/api/v1/serials/warranty-check", json={
        "serial_number": sample_payload["serial_number"],
        "check_date": "2023-01-01"
    })
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_by_product(client: AsyncClient, sample_payload):
    await client.post("/api/v1/serials", json=sample_payload)

    response = await client.get("/api/v1/serials/by-product", params={"code": sample_payload["product_code"]})
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_get_by_customer(client: AsyncClient, sample_payload):
    response = await client.get("/api/v1/serials/by-customer", params={"code": "UNKNOWN"})
    assert response.status_code == 200
    assert len(response.json()) == 0

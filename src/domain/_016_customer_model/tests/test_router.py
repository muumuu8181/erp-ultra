import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.domain._016_customer_model.router import router
from src.foundation._001_database.engine import get_db

app = FastAPI()
app.include_router(router)

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_create_customer_api(client: AsyncClient):
    payload = {
        "code": "CUS-R0001",
        "name": "Router Corp",
        "type": "corporate",
        "tax_type": "standard_10"
    }
    response = await client.post("/api/v1/customers/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "CUS-R0001"
    assert data["name"] == "Router Corp"

async def test_get_customer_api(client: AsyncClient):
    payload = {
        "code": "CUS-R0002",
        "name": "Router Corp 2",
        "type": "corporate",
        "tax_type": "standard_10"
    }
    create_resp = await client.post("/api/v1/customers/", json=payload)
    cust_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/customers/{cust_id}")
    assert response.status_code == 200
    assert response.json()["id"] == cust_id

async def test_list_customers_api(client: AsyncClient):
    payload = {
        "code": "CUS-R0003",
        "name": "Router Corp 3",
        "type": "corporate",
        "tax_type": "standard_10"
    }
    await client.post("/api/v1/customers/", json=payload)

    response = await client.get("/api/v1/customers/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

async def test_update_customer_api(client: AsyncClient):
    payload = {
        "code": "CUS-R0004",
        "name": "Router Corp 4",
        "type": "corporate",
        "tax_type": "standard_10"
    }
    create_resp = await client.post("/api/v1/customers/", json=payload)
    cust_id = create_resp.json()["id"]

    update_payload = {"name": "Updated Router Corp"}
    response = await client.put(f"/api/v1/customers/{cust_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Router Corp"

async def test_delete_customer_api(client: AsyncClient):
    payload = {
        "code": "CUS-R0005",
        "name": "Router Corp 5",
        "type": "corporate",
        "tax_type": "standard_10"
    }
    create_resp = await client.post("/api/v1/customers/", json=payload)
    cust_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/customers/{cust_id}")
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    get_resp = await client.get(f"/api/v1/customers/{cust_id}")
    assert get_resp.status_code == 404

async def test_add_remove_contact_api(client: AsyncClient):
    payload = {
        "code": "CUS-R0006",
        "name": "Router Corp 6",
        "type": "corporate",
        "tax_type": "standard_10"
    }
    create_resp = await client.post("/api/v1/customers/", json=payload)
    cust_id = create_resp.json()["id"]

    contact_payload = {
        "name": "Router Contact 1",
        "is_primary": True
    }
    add_resp = await client.post(f"/api/v1/customers/{cust_id}/contacts", json=contact_payload)
    assert add_resp.status_code == 201
    contact_id = add_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/customers/{cust_id}/contacts/{contact_id}")
    assert del_resp.status_code == 204

async def test_search_customers_api(client: AsyncClient):
    payload = {
        "code": "CUS-R0007",
        "name": "FindMe Corp",
        "type": "corporate",
        "tax_type": "standard_10"
    }
    await client.post("/api/v1/customers/", json=payload)

    response = await client.get("/api/v1/customers/search?q=FindMe")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "FindMe Corp"

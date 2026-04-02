import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI

from src.foundation._001_database import get_db
from src.sales._046_customer_portal.router import router

app = FastAPI()
app.include_router(router)

@pytest.fixture
def override_get_db(db: AsyncSession):
    async def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

from httpx import ASGITransport

@pytest.fixture
async def client(override_get_db) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/v1/portal/register",
        json={
            "customer_code": "CUST001",
            "username": "routeruser",
            "email": "router@example.com",
            "password": "Valid1Pass"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "routeruser"

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/v1/portal/register",
        json={
            "customer_code": "CUST001",
            "username": "loginuser",
            "email": "login@example.com",
            "password": "Valid1Pass"
        }
    )

    response = await client.post(
        "/api/v1/portal/login",
        json={
            "username": "loginuser",
            "password": "Valid1Pass"
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()

@pytest.mark.asyncio
async def test_get_dashboard(client: AsyncClient):
    register_resp = await client.post(
        "/api/v1/portal/register",
        json={
            "customer_code": "CUST001",
            "username": "dashuser",
            "email": "dash@example.com",
            "password": "Valid1Pass"
        }
    )
    user_id = register_resp.json()["id"]

    response = await client.get(
        "/api/v1/portal/dashboard",
        headers={"X-User-Id": str(user_id)}
    )
    assert response.status_code == 200
    assert response.json()["customer_code"] == "CUST001"

@pytest.mark.asyncio
async def test_get_orders(client: AsyncClient):
    register_resp = await client.post(
        "/api/v1/portal/register",
        json={
            "customer_code": "CUST001",
            "username": "orderuser",
            "email": "order@example.com",
            "password": "Valid1Pass"
        }
    )
    user_id = register_resp.json()["id"]

    response = await client.get(
        "/api/v1/portal/orders",
        headers={"X-User-Id": str(user_id)}
    )
    assert response.status_code == 200
    assert response.json()["total_count"] == 0

@pytest.mark.asyncio
async def test_get_invoices(client: AsyncClient):
    register_resp = await client.post(
        "/api/v1/portal/register",
        json={
            "customer_code": "CUST001",
            "username": "invuser",
            "email": "inv@example.com",
            "password": "Valid1Pass"
        }
    )
    user_id = register_resp.json()["id"]

    response = await client.get(
        "/api/v1/portal/invoices",
        headers={"X-User-Id": str(user_id)}
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0

@pytest.mark.asyncio
async def test_change_password(client: AsyncClient):
    register_resp = await client.post(
        "/api/v1/portal/register",
        json={
            "customer_code": "CUST001",
            "username": "pwuser",
            "email": "pw@example.com",
            "password": "Old1Pass"
        }
    )
    user_id = register_resp.json()["id"]

    response = await client.post(
        "/api/v1/portal/change-password",
        json={
            "current_password": "Old1Pass",
            "new_password": "New1Pass"
        },
        headers={"X-User-Id": str(user_id)}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_reset_password(client: AsyncClient):
    await client.post(
        "/api/v1/portal/register",
        json={
            "customer_code": "CUST001",
            "username": "resetuser",
            "email": "reset@example.com",
            "password": "Valid1Pass"
        }
    )

    response = await client.post(
        "/api/v1/portal/reset-password",
        json={"email": "reset@example.com"}
    )
    assert response.status_code == 200
    assert "token" in response.json()

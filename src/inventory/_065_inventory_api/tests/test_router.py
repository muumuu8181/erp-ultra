import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from shared.types import Base
from foundation._001_database.engine import get_db
from src.inventory._065_inventory_api.router import router

app = FastAPI()
app.include_router(router)

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest.mark.asyncio
async def test_create_endpoint():
    response = client.post(
        "/api/v1/inventory-api/",
        json={"name": "Test Router", "path": "/api/router", "method": "POST"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Router"
    assert data["path"] == "/api/router"

@pytest.mark.asyncio
async def test_list_endpoints():
    client.post("/api/v1/inventory-api/", json={"name": "Test 1", "path": "/api/1", "method": "GET"})
    client.post("/api/v1/inventory-api/", json={"name": "Test 2", "path": "/api/2", "method": "GET"})

    response = client.get("/api/v1/inventory-api/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

@pytest.mark.asyncio
async def test_get_endpoint():
    create_response = client.post(
        "/api/v1/inventory-api/",
        json={"name": "Test Get", "path": "/api/get", "method": "GET"}
    )
    endpoint_id = create_response.json()["id"]

    response = client.get(f"/api/v1/inventory-api/{endpoint_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Get"

@pytest.mark.asyncio
async def test_update_endpoint():
    create_response = client.post(
        "/api/v1/inventory-api/",
        json={"name": "Test Update", "path": "/api/update", "method": "GET"}
    )
    endpoint_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/inventory-api/{endpoint_id}",
        json={"name": "Updated API"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated API"

@pytest.mark.asyncio
async def test_delete_endpoint():
    create_response = client.post(
        "/api/v1/inventory-api/",
        json={"name": "Test Delete", "path": "/api/delete", "method": "GET"}
    )
    endpoint_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/inventory-api/{endpoint_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/inventory-api/{endpoint_id}")
    assert get_response.status_code == 404

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import engine, async_session_factory, get_db
from shared.types import Base

from src.inventory._057_warehouse_mgmt.router import router

app = FastAPI()
app.include_router(router)

pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

async def test_create_operation_router(client):
    payload = {
        "operation_number": "OP-ROUT-1",
        "warehouse_code": "WH-R1",
        "operation_type": "put_away",
        "reference_type": "po",
        "reference_number": "PO-1",
        "assigned_to": "user1",
        "priority": "high",
        "created_by": "system",
        "tasks": [
            {
                "task_number": 1,
                "product_code": "P1",
                "product_name": "P1",
                "quantity": 10,
                "from_bin": "A",
                "to_bin": "B"
            }
        ]
    }
    response = await client.post("/api/v1/warehouse-operations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["operation_number"] == "OP-ROUT-1"
    assert data["status"] == "pending"

async def test_get_operation_router(client):
    # Fetch the one we just created
    response = await client.get("/api/v1/warehouse-operations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    op_id = data["items"][0]["id"]

    response = await client.get(f"/api/v1/warehouse-operations/{op_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == op_id

async def test_update_operation_router(client):
    # Fetch list
    response = await client.get("/api/v1/warehouse-operations")
    op_id = response.json()["items"][0]["id"]

    payload = {
        "assigned_to": "user2",
        "priority": "urgent",
        "notes": "Updated note"
    }
    response = await client.put(f"/api/v1/warehouse-operations/{op_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_to"] == "user2"
    assert data["priority"] == "urgent"
    assert data["notes"] == "Updated note"

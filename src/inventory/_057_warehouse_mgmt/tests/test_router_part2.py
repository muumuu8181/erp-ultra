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

async def test_action_endpoints(client):
    # 1. Create op
    payload = {
        "operation_number": "OP-ROUT-2",
        "warehouse_code": "WH-R2",
        "operation_type": "pick",
        "reference_type": "so",
        "reference_number": "SO-2",
        "assigned_to": "user1",
        "created_by": "system",
        "tasks": [
            {
                "task_number": 1,
                "product_code": "P1",
                "product_name": "P1",
                "quantity": 10,
                "from_bin": "A",
            }
        ]
    }
    res = await client.post("/api/v1/warehouse-operations", json=payload)
    op_id = res.json()["id"]
    task_id = res.json()["tasks"][0]["id"]

    # 2. Start
    res = await client.post(f"/api/v1/warehouse-operations/{op_id}/start")
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"

    # 3. Complete Task
    res = await client.post(f"/api/v1/warehouse-operations/{op_id}/tasks/{task_id}/complete")
    assert res.status_code == 200
    # Auto-completes because it's the only task
    assert res.json()["status"] == "completed"

async def test_cancel_endpoint(client):
    payload = {
        "operation_number": "OP-ROUT-3",
        "warehouse_code": "WH-R3",
        "operation_type": "pick",
        "reference_type": "so",
        "reference_number": "SO-3",
        "assigned_to": "user1",
        "created_by": "system",
        "tasks": [
            {
                "task_number": 1,
                "product_code": "P1",
                "product_name": "P1",
                "quantity": 10,
                "from_bin": "A",
            }
        ]
    }
    res = await client.post("/api/v1/warehouse-operations", json=payload)
    op_id = res.json()["id"]

    res = await client.post(f"/api/v1/warehouse-operations/{op_id}/cancel", json={"reason": "Test"})
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"

async def test_pick_list_endpoint(client):
    payload = {
        "warehouse_code": "WH-R4",
        "reference_type": "so",
        "reference_number": "SO-4",
        "assigned_to": "user1"
    }
    res = await client.post("/api/v1/warehouse-operations/pick-list", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "tasks" in data
    assert "total_items" in data

async def test_productivity_endpoint(client):
    res = await client.get("/api/v1/warehouse-operations/productivity?warehouse_code=WH-R2&date_from=2020-01-01&date_to=2030-01-01")
    assert res.status_code == 200
    data = res.json()
    assert "operations_per_hour" in data

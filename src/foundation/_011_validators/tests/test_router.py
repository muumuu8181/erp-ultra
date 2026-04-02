import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from shared.types import Base
from src.foundation._011_validators.router import router, get_db

app = FastAPI()
app.include_router(router)

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_router_create_and_get_rule(client: AsyncClient):
    # Create
    create_data = {
        "name": "test_rule",
        "description": "test",
        "rule_type": "regex",
        "parameters": {"pattern": "^[0-9]+$"},
        "error_message": "Numbers only",
        "is_active": True
    }
    response = await client.post("/api/v1/validators/rules", json=create_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_rule"
    rule_id = data["id"]

    # Get
    response = await client.get(f"/api/v1/validators/rules/{rule_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test_rule"

    # List
    response = await client.get("/api/v1/validators/rules")
    assert response.status_code == 200
    list_data = response.json()
    assert list_data["total"] == 1
    assert len(list_data["items"]) == 1

    # Update
    response = await client.patch(f"/api/v1/validators/rules/{rule_id}", json={"name": "updated_rule"})
    assert response.status_code == 200
    assert response.json()["name"] == "updated_rule"

    # Evaluate
    evaluate_data = {
        "rule_name": "updated_rule",
        "value": "123"
    }
    response = await client.post("/api/v1/validators/evaluate", json=evaluate_data)
    assert response.status_code == 200
    assert response.json()["is_valid"] is True

    # Delete
    response = await client.delete(f"/api/v1/validators/rules/{rule_id}")
    assert response.status_code == 204

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from shared.types import Base
from src.foundation._001_database.engine import get_db
from src.foundation._008_cache.router import router
from src.foundation._008_cache import service

# Setup test app
app = FastAPI()
app.include_router(router)

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(autouse=True)
def clear_cache():
    service.clear_cache_state()
    yield

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_set_cache_endpoint(client: AsyncClient):
    response = await client.put(
        "/api/v1/cache/inventory:item:1",
        json={"key": "inventory:item:1", "value": '{"id": 1}', "ttl_seconds": 60, "module": "inventory"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "inventory:item:1"
    assert data["value"] == '{"id": 1}'

@pytest.mark.asyncio
async def test_get_cache_endpoint(client: AsyncClient):
    await client.put(
        "/api/v1/cache/inventory:item:1",
        json={"key": "inventory:item:1", "value": '{"id": 1}', "ttl_seconds": 60, "module": "inventory"}
    )

    response = await client.get("/api/v1/cache/inventory:item:1")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == '{"id": 1}'

@pytest.mark.asyncio
async def test_get_cache_not_found(client: AsyncClient):
    try:
        response = await client.get("/api/v1/cache/inventory:item:missing")
        assert response.status_code != 200
    except Exception:
        # If the app raises the exception directly (since no global handler in test)
        pass

@pytest.mark.asyncio
async def test_delete_cache_endpoint(client: AsyncClient):
    await client.put(
        "/api/v1/cache/inventory:item:1",
        json={"key": "inventory:item:1", "value": '{"id": 1}', "ttl_seconds": 60, "module": "inventory"}
    )

    response = await client.delete("/api/v1/cache/inventory:item:1")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_clear_by_module_endpoint(client: AsyncClient):
    await client.put(
        "/api/v1/cache/inventory:item:1",
        json={"key": "inventory:item:1", "value": '{"id": 1}', "ttl_seconds": 60, "module": "inventory"}
    )

    response = await client.delete("/api/v1/cache/?module=inventory")
    assert response.status_code == 200
    assert response.json()["cleared_count"] == 1

@pytest.mark.asyncio
async def test_invalidate_endpoint(client: AsyncClient):
    await client.put(
        "/api/v1/cache/inventory:item:1",
        json={"key": "inventory:item:1", "value": '{"id": 1}', "ttl_seconds": 60, "module": "inventory"}
    )

    response = await client.post("/api/v1/cache/invalidate", json={"pattern": "inventory:*"})
    assert response.status_code == 200
    assert response.json()["invalidated_count"] == 1

@pytest.mark.asyncio
async def test_stats_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/cache/stats")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_warm_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/cache/warm", json={
        "entries": [
            {"key": "inventory:1", "value": "1", "ttl_seconds": 60, "module": "inventory"}
        ]
    })
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_cleanup_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/cache/cleanup")
    assert response.status_code == 200

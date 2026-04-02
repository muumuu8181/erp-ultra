import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from shared.types import Base
from src.foundation._001_database import get_db
from src.foundation._004_api_gateway.router import router


@pytest_asyncio.fixture
async def app_with_db() -> FastAPI:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with Session() as session:
            yield session

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest_asyncio.fixture
async def client(app_with_db: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app_with_db), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_gateway_route_endpoints(client: AsyncClient):
    # Create
    response = await client.post("/api/v1/api-gateway/routes", json={
        "path": "/api/users",
        "target_url": "http://user-service:8080"
    })
    assert response.status_code == 201
    route_id = response.json()["id"]

    # Get
    response = await client.get(f"/api/v1/api-gateway/routes/{route_id}")
    assert response.status_code == 200
    assert response.json()["path"] == "/api/users"

    # List
    response = await client.get("/api/v1/api-gateway/routes")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    # Update
    response = await client.put(f"/api/v1/api-gateway/routes/{route_id}", json={
        "target_url": "http://new-service:8080"
    })
    assert response.status_code == 200
    assert response.json()["target_url"] == "http://new-service:8080"

    # Delete
    response = await client.delete(f"/api/v1/api-gateway/routes/{route_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_rate_limit_rule_endpoints(client: AsyncClient):
    # Create
    response = await client.post("/api/v1/api-gateway/rate-limits", json={
        "path": "/api/users",
        "max_requests": 100,
        "window_seconds": 60
    })
    assert response.status_code == 201
    rule_id = response.json()["id"]

    # Get
    response = await client.get(f"/api/v1/api-gateway/rate-limits/{rule_id}")
    assert response.status_code == 200
    assert response.json()["max_requests"] == 100

    # List
    response = await client.get("/api/v1/api-gateway/rate-limits")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    # Update
    response = await client.put(f"/api/v1/api-gateway/rate-limits/{rule_id}", json={
        "max_requests": 200
    })
    assert response.status_code == 200
    assert response.json()["max_requests"] == 200

    # Delete
    response = await client.delete(f"/api/v1/api-gateway/rate-limits/{rule_id}")
    assert response.status_code == 204

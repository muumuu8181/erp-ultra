import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.domain._030_attachment.router import router
from src.foundation._001_database import get_db
from shared.types import Base

@pytest.fixture
async def app_with_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with Session() as session:
            yield session

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.fixture
async def client(app_with_db):
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_create_attachment_endpoint(client: AsyncClient):
    data = {"code": "RTR-01", "name": "router_test.pdf"}
    resp = await client.post("/api/v1/attachment", json=data)
    assert resp.status_code == 201
    result = resp.json()
    assert result["code"] == "RTR-01"
    assert "id" in result

@pytest.mark.asyncio
async def test_get_attachment_endpoint(client: AsyncClient):
    data = {"code": "RTR-02", "name": "router_test2.pdf"}
    create_resp = await client.post("/api/v1/attachment", json=data)
    created_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/attachment/{created_id}")
    assert resp.status_code == 200
    result = resp.json()
    assert result["id"] == created_id
    assert result["code"] == "RTR-02"

@pytest.mark.asyncio
async def test_get_attachment_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/attachment/999")
    assert resp.status_code == 404

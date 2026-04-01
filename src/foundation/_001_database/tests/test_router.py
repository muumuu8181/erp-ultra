"""Tests for 001_database router."""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from src.foundation._001_database.router import router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestDatabaseRouter:
    async def test_health_endpoint(self, client: AsyncClient):
        resp = await client.get("/api/v1/database/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "error")

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from src.foundation._014_middleware.router import router


@pytest.fixture
def app():
    fastapi_app = FastAPI()
    fastapi_app.include_router(router)
    return fastapi_app


@pytest.mark.asyncio
async def test_get_middleware_config(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/middleware/config")

    assert response.status_code == 200
    data = response.json()
    assert "middleware" in data
    assert "config" in data

    assert isinstance(data["middleware"], list)
    assert isinstance(data["config"], dict)

    assert "timing_enabled" in data["config"]
    assert "request_id_enabled" in data["config"]

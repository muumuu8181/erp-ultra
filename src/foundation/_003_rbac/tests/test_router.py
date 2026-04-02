import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database import get_db
from src.foundation._003_rbac.router import router

app = FastAPI()
app.include_router(router)

@pytest.fixture
def override_get_db(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_role_endpoint(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/rbac/roles",
            json={"name": "viewer", "description": "Viewer role", "is_active": True}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "viewer"
        assert "id" in data

@pytest.mark.asyncio
async def test_get_roles_endpoint(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/rbac/roles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_create_permission_endpoint(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/rbac/permissions",
            json={"resource": "comments", "action": "delete", "effect": "deny"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["resource"] == "comments"
        assert data["effect"] == "deny"

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.domain._031_audit_log.router import router
from src.foundation._001_database.engine import create_engine, get_session_factory, get_db
from shared.types import Base

@pytest.fixture
async def db_session():
    test_engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        yield session

@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_router_audit_log(client: AsyncClient):
    # Create
    create_data = {
        "action": "CREATE",
        "entity_name": "Invoice",
        "entity_id": "inv_1",
        "user_id": "user_1"
    }
    response = await client.post("/api/v1/audit-log/", json=create_data)
    assert response.status_code == 201
    data = response.json()
    assert data["action"] == "CREATE"
    audit_log_id = data["id"]

    # Get
    response = await client.get(f"/api/v1/audit-log/{audit_log_id}")
    assert response.status_code == 200
    assert response.json()["id"] == audit_log_id

    # List
    response = await client.get("/api/v1/audit-log/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # Update
    update_data = {"action": "UPDATE"}
    response = await client.put(f"/api/v1/audit-log/{audit_log_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["action"] == "UPDATE"

    # Delete
    response = await client.delete(f"/api/v1/audit-log/{audit_log_id}")
    assert response.status_code == 204

    # Verify deletion
    response = await client.get(f"/api/v1/audit-log/{audit_log_id}")
    assert response.status_code == 404

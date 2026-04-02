import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.foundation._010_event_bus.router import router
from src.foundation._001_database.engine import get_db

app = FastAPI()
app.include_router(router)

@pytest.fixture
def override_get_db(db_session):
    async def _override():
        yield db_session
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_publish_endpoint(async_client):
    response = await async_client.post(
        "/api/v1/events/publish",
        json={"event_type": "test.event", "source_module": "test", "payload": {}}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "test.event"
    assert data["status"] == "processed"

@pytest.mark.asyncio
async def test_publish_endpoint_invalid_type(async_client):
    response = await async_client.post(
        "/api/v1/events/publish",
        json={"event_type": "invalid", "source_module": "test", "payload": {}}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_list_events(async_client):
    await async_client.post(
        "/api/v1/events/publish",
        json={"event_type": "test.event", "source_module": "test", "payload": {}}
    )
    response = await async_client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

@pytest.mark.asyncio
async def test_get_event(async_client):
    pub = await async_client.post(
        "/api/v1/events/publish",
        json={"event_type": "test.event", "source_module": "test", "payload": {}}
    )
    event_id = pub.json()["id"]

    response = await async_client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["id"] == event_id

@pytest.mark.asyncio
async def test_get_event_not_found(async_client):
    from shared.errors import NotFoundError
    with pytest.raises(NotFoundError):
        await async_client.get("/api/v1/events/999")

@pytest.mark.asyncio
async def test_subscriptions_endpoints(async_client):
    res1 = await async_client.post(
        "/api/v1/events/subscriptions",
        json={"event_type": "test.*", "handler_module": "test_mod", "handler_function": "func"}
    )
    assert res1.status_code == 201

    res2 = await async_client.get("/api/v1/events/subscriptions")
    assert res2.status_code == 200
    assert len(res2.json()) >= 1

@pytest.mark.asyncio
async def test_replay_endpoint(async_client):
    pub = await async_client.post(
        "/api/v1/events/publish",
        json={"event_type": "test.event", "source_module": "test", "payload": {}}
    )
    event_id = pub.json()["id"]

    res = await async_client.post(f"/api/v1/events/{event_id}/replay")
    assert res.status_code == 200
    assert res.json()["id"] != event_id

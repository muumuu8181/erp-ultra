import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.types import Base
from src.foundation._001_database.engine import get_db
from src.foundation._007_queue.router import router
from src.foundation._007_queue.schemas import QueueMessageCreate
from src.foundation._007_queue.service import clear_queue_state, enqueue

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

app = FastAPI()
app.include_router(router)

async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    clear_queue_state()

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_enqueue_endpoint(client: AsyncClient):
    response = await client.post(
        "/api/v1/queue/queues/orders/messages",
        json={"payload": '{"order": 1}', "priority": 0, "max_retries": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["queue_name"] == "orders"
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_dequeue_endpoint(client: AsyncClient, db: AsyncSession):
    await enqueue(db, "orders", QueueMessageCreate(payload='{"order": 1}'))

    response = await client.post("/api/v1/queue/queues/orders/dequeue", json={"max_messages": 1})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "processing"

@pytest.mark.asyncio
async def test_complete_endpoint(client: AsyncClient, db: AsyncSession):
    msg = await enqueue(db, "orders", QueueMessageCreate(payload='{"order": 1}'))

    response = await client.post(f"/api/v1/queue/messages/{msg.id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

@pytest.mark.asyncio
async def test_fail_endpoint(client: AsyncClient, db: AsyncSession):
    msg = await enqueue(db, "orders", QueueMessageCreate(payload='{"order": 1}'))

    response = await client.post(
        f"/api/v1/queue/messages/{msg.id}/fail",
        json={"error_message": "failed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["retry_count"] == 1

@pytest.mark.asyncio
async def test_queue_stats_endpoint(client: AsyncClient, db: AsyncSession):
    await enqueue(db, "orders", QueueMessageCreate(payload='{"order": 1}'))

    response = await client.get("/api/v1/queue/queues/orders/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["pending_count"] == 1
    assert data["total_count"] == 1

@pytest.mark.asyncio
async def test_purge_endpoint(client: AsyncClient, db: AsyncSession):
    await enqueue(db, "orders", QueueMessageCreate(payload='{"order": 1}'))

    response = await client.delete("/api/v1/queue/queues/orders/purge")
    assert response.status_code == 200
    data = response.json()
    assert data["purged_count"] == 1

@pytest.mark.asyncio
async def test_dead_letters_endpoint(client: AsyncClient, db: AsyncSession):
    msg = await enqueue(db, "orders", QueueMessageCreate(payload='{"order": 1}', max_retries=1))
    await client.post(f"/api/v1/queue/queues/orders/dequeue", json={"max_messages": 1})
    await client.post(f"/api/v1/queue/messages/{msg.id}/fail", json={"error_message": "failed"})

    response = await client.get("/api/v1/queue/dead-letters?queue_name=orders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

@pytest.mark.asyncio
async def test_enqueue_invalid_payload(client: AsyncClient):
    # In a full app there's usually an exception handler mapping ValidationError to 422.
    # Since our test app doesn't have it, a shared.errors.ValidationError will crash the request with a 500,
    # and the ASGI client bubbles up the Exception. We will catch the exception directly.
    from shared.errors import ValidationError
    with pytest.raises(ValidationError):
        await client.post(
            "/api/v1/queue/queues/orders/messages",
            json={"payload": "invalid json", "priority": 0, "max_retries": 3}
        )

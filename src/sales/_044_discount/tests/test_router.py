import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.sales._044_discount.router import router
from src.foundation._001_database.engine import get_db
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from shared.types import Base

# Create app and bind router
app = FastAPI()
app.include_router(router)

@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session

@pytest.fixture
def override_get_db(db_session):
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
async def client(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_discount_rule(client: AsyncClient):
    payload = {
        "name": "Router Test",
        "code": "ROUT01",
        "discount_type": "percentage",
        "value": "10.0",
        "applies_to": "order_total",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "is_stackable": True,
        "is_active": True
    }
    response = await client.post("/api/v1/discount-rules", json=payload)
    assert response.status_code == 201
    assert response.json()["code"] == "ROUT01"

@pytest.mark.asyncio
async def test_list_discount_rules(client: AsyncClient):
    response = await client.get("/api/v1/discount-rules")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

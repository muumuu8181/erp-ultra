import pytest
from httpx import AsyncClient, ASGITransport
from datetime import date
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from shared.types import Base
from src.domain._028_pricing.models import PriceList, PriceListItem

from src.domain._028_pricing.router import router

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(DATABASE_URL, echo=False, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(router)
    from src.foundation._001_database import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    return app

from decimal import Decimal

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

async def test_create_price_list(client: AsyncClient):
    data = {
        "name": "Router Test",
        "code": "R_TEST_01",
        "valid_from": "2023-01-01",
        "currency_code": "JPY",
        "is_active": True
    }
    response = await client.post("/api/v1/price-lists", json=data)
    assert response.status_code == 201
    assert response.json()["code"] == "R_TEST_01"

async def test_list_price_lists(client: AsyncClient):
    response = await client.get("/api/v1/price-lists")
    assert response.status_code == 200
    assert "items" in response.json()

async def test_update_price_list(client: AsyncClient):
    data = {
        "name": "Router Test Update",
        "code": "R_TEST_02",
        "valid_from": "2023-01-01",
        "currency_code": "JPY",
        "is_active": True
    }
    create_resp = await client.post("/api/v1/price-lists", json=data)
    pl_id = create_resp.json()["id"]

    update_data = {
        "name": "Router Test Updated Name",
        "code": "R_TEST_02",
        "valid_from": "2023-01-01",
        "currency_code": "JPY",
        "is_active": False
    }
    response = await client.put(f"/api/v1/price-lists/{pl_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Router Test Updated Name"

async def test_add_list_price_item(client: AsyncClient):
    data = {
        "name": "Router Test Items",
        "code": "R_TEST_03",
        "valid_from": "2023-01-01"
    }
    create_resp = await client.post("/api/v1/price-lists", json=data)
    pl_id = create_resp.json()["id"]

    item_data = {
        "product_code": "PROD-R1",
        "unit_price": 100.50,
        "discount_percentage": 0,
        "min_quantity": 1
    }
    response = await client.post(f"/api/v1/price-lists/{pl_id}/items", json=item_data)
    assert response.status_code == 201
    assert response.json()["product_code"] == "PROD-R1"

    list_resp = await client.get(f"/api/v1/price-lists/{pl_id}/items")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) >= 1

async def test_lookup_and_best_price(client: AsyncClient):
    data1 = {"name": "Router Lookup 1", "code": "R_LOOK_1", "valid_from": "2023-01-01"}
    data2 = {"name": "Router Lookup 2", "code": "R_LOOK_2", "valid_from": "2023-01-01"}

    pl1 = await client.post("/api/v1/price-lists", json=data1)
    pl2 = await client.post("/api/v1/price-lists", json=data2)

    await client.post(f"/api/v1/price-lists/{pl1.json()['id']}/items", json={
        "product_code": "PROD-LOOK", "unit_price": 100, "min_quantity": 1, "discount_percentage": 0
    })
    await client.post(f"/api/v1/price-lists/{pl2.json()['id']}/items", json={
        "product_code": "PROD-LOOK", "unit_price": 80, "min_quantity": 1, "discount_percentage": 0
    })

    req_data = {
        "product_code": "PROD-LOOK",
        "quantity": 5,
        "date": "2023-02-01",
        "price_list_id": None
    }

    lookup_resp = await client.post("/api/v1/pricing/lookup", json=req_data)
    if lookup_resp.status_code != 200:
        print("lookup error", lookup_resp.json())
    assert lookup_resp.status_code == 200

    best_resp = await client.post("/api/v1/pricing/best-price", json=req_data)
    if best_resp.status_code != 200:
        print("best price error", best_resp.json())
    assert best_resp.status_code == 200
    assert float(best_resp.json()["unit_price"]) == 80.0

async def test_duplicate_price_list(client: AsyncClient):
    data = {"name": "Router Dup Src", "code": "R_DUP_S", "valid_from": "2023-01-01"}
    create_resp = await client.post("/api/v1/price-lists", json=data)
    pl_id = create_resp.json()["id"]

    dup_data = {"new_code": "R_DUP_T", "new_name": "Router Dup Tgt"}
    dup_resp = await client.post(f"/api/v1/price-lists/{pl_id}/duplicate", json=dup_data)
    assert dup_resp.status_code == 201
    assert dup_resp.json()["code"] == "R_DUP_T"

async def test_invalid_date_range(client: AsyncClient):
    data = {
        "name": "Invalid Dates",
        "code": "R_INV_DATES",
        "valid_from": "2023-12-31",
        "valid_to": "2023-01-01"
    }
    response = await client.post("/api/v1/price-lists", json=data)
    assert response.status_code == 422

async def test_duplicate_code(client: AsyncClient):
    data = {"name": "Dup Code", "code": "R_DUP_C", "valid_from": "2023-01-01"}
    await client.post("/api/v1/price-lists", json=data)
    response = await client.post("/api/v1/price-lists", json=data)
    assert response.status_code == 409

async def test_missing_price_list(client: AsyncClient):
    item_data = {"product_code": "P1", "unit_price": 100, "min_quantity": 1, "discount_percentage": 0}
    response = await client.post("/api/v1/price-lists/9999/items", json=item_data)
    assert response.status_code == 404

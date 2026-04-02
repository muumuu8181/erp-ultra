import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from src.inventory._063_bom_inventory.router import router
from src.foundation._001_database import get_db
from shared.types import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Setup test DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# Setup app
app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(setup_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_bom_api(client: AsyncClient):
    response = await client.post(
        "/api/v1/bom_inventory/boms",
        json={"product_id": "P-01", "quantity": 1, "status": "active", "version": 1}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == "P-01"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_bom_api(client: AsyncClient):
    # create
    create_response = await client.post(
        "/api/v1/bom_inventory/boms",
        json={"product_id": "P-01"}
    )
    bom_id = create_response.json()["id"]

    # get
    response = await client.get(f"/api/v1/bom_inventory/boms/{bom_id}")
    assert response.status_code == 200
    assert response.json()["product_id"] == "P-01"


@pytest.mark.asyncio
async def test_list_boms_api(client: AsyncClient):
    # create two
    await client.post("/api/v1/bom_inventory/boms", json={"product_id": "P-01"})
    await client.post("/api/v1/bom_inventory/boms", json={"product_id": "P-02"})

    response = await client.get("/api/v1/bom_inventory/boms")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_update_bom_api(client: AsyncClient):
    create_response = await client.post("/api/v1/bom_inventory/boms", json={"product_id": "P-01"})
    bom_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/bom_inventory/boms/{bom_id}",
        json={"product_id": "P-02", "status": "obsolete"}
    )
    assert response.status_code == 200
    assert response.json()["product_id"] == "P-02"


from shared.errors import NotFoundError

@pytest.mark.asyncio
async def test_delete_bom_api(client: AsyncClient):
    create_response = await client.post("/api/v1/bom_inventory/boms", json={"product_id": "P-01"})
    bom_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/bom_inventory/boms/{bom_id}")
    assert response.status_code == 204

    with pytest.raises(NotFoundError):
        await client.get(f"/api/v1/bom_inventory/boms/{bom_id}")


@pytest.mark.asyncio
async def test_add_bom_item_api(client: AsyncClient):
    create_response = await client.post("/api/v1/bom_inventory/boms", json={"product_id": "P-01"})
    bom_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/bom_inventory/boms/{bom_id}/items",
        json={"component_id": "C-01", "quantity_required": 5}
    )
    assert response.status_code == 201
    assert response.json()["component_id"] == "C-01"


@pytest.mark.asyncio
async def test_remove_bom_item_api(client: AsyncClient):
    create_bom_response = await client.post("/api/v1/bom_inventory/boms", json={"product_id": "P-01"})
    bom_id = create_bom_response.json()["id"]

    create_item_response = await client.post(
        f"/api/v1/bom_inventory/boms/{bom_id}/items",
        json={"component_id": "C-01", "quantity_required": 5}
    )
    item_id = create_item_response.json()["id"]

    response = await client.delete(f"/api/v1/bom_inventory/boms/{bom_id}/items/{item_id}")
    assert response.status_code == 204

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from shared.types import Base
from shared.errors import NotFoundError, DuplicateError
from src.inventory._065_inventory_api.schemas import InventoryEndpointCreate, InventoryEndpointUpdate
from src.inventory._065_inventory_api import service

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session

@pytest.mark.asyncio
async def test_create_and_get_endpoint(db_session: AsyncSession):
    endpoint_in = InventoryEndpointCreate(
        name="Test Create",
        path="/test/create",
        method="GET"
    )
    created = await service.create_inventory_endpoint(db_session, endpoint_in)
    assert created.id is not None
    assert created.name == "Test Create"

    fetched = await service.get_inventory_endpoint(db_session, created.id)
    assert fetched.id == created.id
    assert fetched.path == "/test/create"

@pytest.mark.asyncio
async def test_create_duplicate_endpoint(db_session: AsyncSession):
    endpoint_in = InventoryEndpointCreate(
        name="Test Dup",
        path="/test/dup",
        method="GET"
    )
    await service.create_inventory_endpoint(db_session, endpoint_in)

    with pytest.raises(DuplicateError):
        await service.create_inventory_endpoint(db_session, endpoint_in)

@pytest.mark.asyncio
async def test_get_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await service.get_inventory_endpoint(db_session, 999)

@pytest.mark.asyncio
async def test_update_endpoint(db_session: AsyncSession):
    endpoint_in = InventoryEndpointCreate(
        name="Test Update",
        path="/test/update",
        method="GET"
    )
    created = await service.create_inventory_endpoint(db_session, endpoint_in)

    update_in = InventoryEndpointUpdate(name="Updated Name", is_active=False)
    updated = await service.update_inventory_endpoint(db_session, created.id, update_in)

    assert updated.name == "Updated Name"
    assert updated.is_active is False
    assert updated.path == "/test/update"

@pytest.mark.asyncio
async def test_delete_endpoint(db_session: AsyncSession):
    endpoint_in = InventoryEndpointCreate(
        name="Test Delete",
        path="/test/delete",
        method="GET"
    )
    created = await service.create_inventory_endpoint(db_session, endpoint_in)

    await service.delete_inventory_endpoint(db_session, created.id)

    with pytest.raises(NotFoundError):
        await service.get_inventory_endpoint(db_session, created.id)

@pytest.mark.asyncio
async def test_get_endpoints_paginated(db_session: AsyncSession):
    for i in range(5):
        await service.create_inventory_endpoint(
            db_session,
            InventoryEndpointCreate(name=f"Test {i}", path=f"/test/{i}", method="GET")
        )

    response = await service.get_inventory_endpoints(db_session, skip=0, limit=2)
    assert response.total == 5
    assert len(response.items) == 2
    assert response.page == 1
    assert response.total_pages == 3

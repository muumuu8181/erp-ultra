import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI
from src.foundation._001_database.engine import create_engine, get_session_factory, get_db
from src.domain._035_localization.router import router
from shared.types import Base

# Setup in-memory sqlite
test_engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
session_factory = get_session_factory(test_engine)

@pytest.fixture(autouse=True)
async def init_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session():
    async with session_factory() as session:
        yield session

@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    # Override db
    async def override_get_db():
        async with session_factory() as session:
            yield session
    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

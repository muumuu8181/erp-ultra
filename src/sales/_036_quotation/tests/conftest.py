import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI

from src.foundation._001_database.engine import create_engine, get_session_factory, get_db
from shared.types import Base
from src.sales._036_quotation.router import router

app = FastAPI()
app.include_router(router)

test_engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = get_session_factory(test_engine)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provide a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    """Provide a test client for FastAPI."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

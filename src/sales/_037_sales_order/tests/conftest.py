import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from shared.types import Base
from src.foundation._001_database import get_db
from src.sales._037_sales_order.router import router

# Setup in-memory SQLite for testing
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

import pytest_asyncio

@pytest_asyncio.fixture(scope="function")
async def in_memory_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest_asyncio.fixture(scope="function")
async def client(app, in_memory_db):
    async def override_get_db():
        yield in_memory_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

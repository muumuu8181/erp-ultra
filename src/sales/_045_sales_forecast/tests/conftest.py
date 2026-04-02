import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from shared.types import Base
from src.foundation._001_database.engine import get_db

from fastapi import FastAPI
from src.sales._045_sales_forecast.router import router as sales_forecast_router

# Configure testing app
app = FastAPI()
app.include_router(sales_forecast_router)

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(setup_db):
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    # Override get_db dependency to use the test session
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.foundation._001_database.engine import create_engine, get_session_factory, get_db
from src.domain._035_localization.models import BaseModel
from src.domain._035_localization.router import router
from fastapi import FastAPI


app = FastAPI()
app.include_router(router)


@pytest.fixture
async def db_engine():
    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    session_factory = get_session_factory(db_engine)
    async with session_factory() as session:
        yield session


from httpx import ASGITransport

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

"""
Tests for migration router endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from unittest.mock import patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.types import Base
from src.foundation._001_database.engine import get_db
from src.foundation._009_migration.router import router
from src.foundation._009_migration.models import MigrationRecord

TEST_DB_URL = "sqlite+aiosqlite://"

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

from fastapi.responses import JSONResponse
from shared.errors import ERPError, ValidationError, DuplicateError, BusinessRuleError, NotFoundError

@pytest.fixture
def app(db_session: AsyncSession):
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(ERPError)
    async def erp_error_handler(request, exc: ERPError):
        status_code = 400
        if isinstance(exc, DuplicateError):
            status_code = 409
        elif isinstance(exc, NotFoundError):
            status_code = 404
        return JSONResponse(status_code=status_code, content={"message": exc.message, "code": exc.code})

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.mark.asyncio
async def test_get_status(app: FastAPI, db_session: AsyncSession):
    # Ensure there's a record to prevent it being None and throwing an issue or just mock it.
    # Actually wait, `get_pending_migrations` attempts to use `_get_alembic_config` which will hit the real disk alembic.ini.
    # Let's patch `service.get_pending_migrations` and others or just let it hit the newly created alembic config.
    pass # we will patch it to keep it purely unit

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.get_pending_migrations")
@patch("src.foundation._009_migration.service.get_current_revision")
@patch("src.foundation._009_migration.service.get_module_status")
async def test_get_status_mocked(mock_mod, mock_cur, mock_pend, app: FastAPI):
    mock_cur.return_value = "abc"
    mock_pend.return_value = []
    mock_mod.return_value = []

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/migrations/status")

    assert response.status_code == 200
    data = response.json()
    assert data["current_revision"] == "abc"
    assert data["is_up_to_date"] is True

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.get_pending_migrations")
async def test_get_pending(mock_pend, app: FastAPI):
    mock_pend.return_value = [{"revision": "abc", "module": "mod", "description": "desc"}]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/migrations/pending")

    assert response.status_code == 200
    assert len(response.json()) == 1

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.apply_migration")
async def test_apply_success(mock_apply, app: FastAPI):
    mock_record = MagicMock()
    mock_record.id = 1
    mock_record.version = "1234567890ab"
    mock_record.module = "_009_migration"
    mock_record.description = "desc"
    mock_record.applied_at = MagicMock()
    mock_record.applied_at.isoformat.return_value = "2024-01-01T00:00:00"
    mock_record.applied_by = "sys"
    mock_apply.return_value = mock_record

    payload = {"revision": "1234567890ab", "module": "_009_migration"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/migrations/apply", json=payload)

    assert response.status_code == 200
    assert response.json()["version"] == "1234567890ab"

@pytest.mark.asyncio
async def test_apply_invalid_format(app: FastAPI):
    payload = {"revision": "invalid"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/migrations/apply", json=payload)
    assert response.status_code == 400

@pytest.mark.asyncio
@patch("src.foundation._009_migration.validators.validate_migration_not_applied")
async def test_apply_duplicate(mock_validate, app: FastAPI):
    mock_validate.side_effect = DuplicateError("Migration", "1234567890ab")
    payload = {"revision": "1234567890ab"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/migrations/apply", json=payload)
    assert response.status_code == 409

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.rollback_migration")
async def test_rollback_success(mock_rollback, app: FastAPI):
    mock_record = MagicMock()
    mock_record.id = 1
    mock_record.version = "1234567890ab"
    mock_record.module = "_009_migration"
    mock_record.description = "desc"
    mock_record.applied_at = MagicMock()
    mock_record.applied_at.isoformat.return_value = "2024-01-01T00:00:00"
    mock_record.applied_by = "sys"
    mock_rollback.return_value = mock_record

    payload = {"revision": "1234567890ab", "module": "_009_migration"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/migrations/rollback", json=payload)

    assert response.status_code == 200
    assert response.json()["version"] == "1234567890ab"

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.get_migration_history")
async def test_history(mock_hist, app: FastAPI):
    mock_hist.return_value = []
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/migrations/history")

    assert response.status_code == 200
    assert response.json() == []

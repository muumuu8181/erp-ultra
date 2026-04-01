"""Tests for 001_database engine and session management."""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import (
    create_engine,
    get_db,
    get_session_factory,
)
from src.foundation._001_database.health import check_db_health


@pytest.fixture
async def db_session():
    """Provide a test database session using in-memory SQLite."""
    test_engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        yield session


class TestCreateEngine:
    async def test_creates_async_engine(self):
        eng = create_engine("sqlite+aiosqlite:///:memory:")
        assert eng is not None
        await eng.dispose()

    async def test_echo_mode(self):
        eng = create_engine("sqlite+aiosqlite:///:memory:", echo=True)
        assert eng.echo is True
        await eng.dispose()


class TestGetDb:
    async def test_yields_session(self):
        test_engine = create_engine("sqlite+aiosqlite:///:memory:")
        session_factory = get_session_factory(test_engine)
        async with session_factory() as session:
            assert isinstance(session, AsyncSession)
            await session.dispose()


class TestHealthCheck:
    async def test_health_ok(self, db_session: AsyncSession):
        result = await check_db_health()
        assert result["status"] == "ok"

    async def test_select_query_works(self, db_session: AsyncSession):
        result = await db_session.execute(text("SELECT 1 AS val"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1

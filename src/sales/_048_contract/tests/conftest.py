import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import create_engine, get_session_factory
from shared.types import Base

@pytest.fixture
async def db_session():
    """Provide a test database session using in-memory SQLite."""
    test_engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        yield session

    await test_engine.dispose()

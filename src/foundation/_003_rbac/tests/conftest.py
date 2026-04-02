import pytest_asyncio

from shared.types import Base
from src.foundation._001_database.engine import create_engine, get_session_factory


@pytest_asyncio.fixture
async def db_session():
    """Provide a test database session using in-memory SQLite and initialize schema."""
    test_engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables in the memory db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        yield session

    await test_engine.dispose()

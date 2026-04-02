"""
Tests for migration validation logic.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.types import Base
from shared.errors import ValidationError, DuplicateError
from src.foundation._009_migration.models import MigrationRecord
from src.foundation._009_migration.validators import (
    validate_revision_format,
    validate_migration_not_applied,
    validate_module_name
)

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

def test_validate_revision_format():
    assert validate_revision_format("1a2b3c4d5e6f") == "1a2b3c4d5e6f"

    with pytest.raises(ValidationError):
        validate_revision_format("invalid")

    with pytest.raises(ValidationError):
        validate_revision_format("1a2b3c4d5e6g")  # not hex

@pytest.mark.asyncio
async def test_validate_migration_not_applied(db_session: AsyncSession):
    db_session.add(MigrationRecord(version="abc", module="mod", description="desc"))
    await db_session.commit()

    # Existing
    with pytest.raises(DuplicateError):
        await validate_migration_not_applied(db_session, "abc")

    # Non-existing shouldn't raise
    await validate_migration_not_applied(db_session, "def")

def test_validate_module_name():
    assert validate_module_name("_009_migration") == "_009_migration"

    with pytest.raises(ValidationError):
        validate_module_name("009_migration")

    with pytest.raises(ValidationError):
        validate_module_name("module_name")

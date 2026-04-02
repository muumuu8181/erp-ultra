"""
Tests for MigrationRecord model.
"""
import pytest
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.types import Base
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

@pytest.mark.asyncio
async def test_migration_record_creation(db_session: AsyncSession):
    record = MigrationRecord(
        version="1234567890ab",
        module="_009_migration",
        description="Test migration"
    )
    db_session.add(record)
    await db_session.commit()

    stmt = select(MigrationRecord).where(MigrationRecord.version == "1234567890ab")
    result = await db_session.execute(stmt)
    saved = result.scalar_one()

    assert saved.module == "_009_migration"
    assert saved.description == "Test migration"
    assert saved.applied_by == "system"
    assert isinstance(saved.applied_at, datetime)
    assert isinstance(saved.created_at, datetime)

@pytest.mark.asyncio
async def test_migration_record_unique_constraint(db_session: AsyncSession):
    record1 = MigrationRecord(version="dup123", module="mod1", description="desc1")
    record2 = MigrationRecord(version="dup123", module="mod2", description="desc2")

    db_session.add(record1)
    await db_session.commit()

    db_session.add(record2)
    with pytest.raises(IntegrityError):
        await db_session.commit()

def test_migration_record_repr():
    record = MigrationRecord(version="abc", module="mod")
    assert repr(record) == "<MigrationRecord abc (mod)>"

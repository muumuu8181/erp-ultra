"""
Tests for migration service logic.
"""
import pytest
from unittest.mock import patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.types import Base
from shared.errors import DuplicateError, NotFoundError, BusinessRuleError
from src.foundation._009_migration.models import MigrationRecord
from src.foundation._009_migration import service

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
async def test_get_current_revision_none(db_session: AsyncSession):
    rev = await service.get_current_revision(db_session)
    assert rev is None

@pytest.mark.asyncio
async def test_get_current_revision_exists(db_session: AsyncSession):
    db_session.add(MigrationRecord(version="abc", module="m", description="desc"))
    await db_session.commit()

    rev = await service.get_current_revision(db_session)
    assert rev == "abc"

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.ScriptDirectory")
@patch("src.foundation._009_migration.service._get_alembic_config")
async def test_get_pending_migrations(mock_cfg, mock_script, db_session: AsyncSession):
    # Setup mock alembic revisions
    mock_rev1 = MagicMock(revision="111", doc="[_009_migration] First")
    mock_rev2 = MagicMock(revision="222", doc="[_009_migration] Second")
    mock_rev3 = MagicMock(revision="333", doc="[other_mod] Third")

    mock_script.from_config.return_value.walk_revisions.return_value = [mock_rev3, mock_rev2, mock_rev1]

    # 222 is already applied
    db_session.add(MigrationRecord(version="222", module="_009_migration", description="Second"))
    await db_session.commit()

    pending = await service.get_pending_migrations(db_session)
    assert len(pending) == 2
    # Should be reversed to chronological
    assert pending[0]["revision"] == "111"
    assert pending[0]["module"] == "_009_migration"
    assert pending[1]["revision"] == "333"

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.get_pending_migrations")
@patch("src.foundation._009_migration.service.command.upgrade")
@patch("src.foundation._009_migration.service._get_alembic_config")
async def test_apply_migration_success(mock_cfg, mock_upgrade, mock_pending, db_session: AsyncSession):
    mock_pending.return_value = [{"revision": "abc", "module": "mod", "description": "desc"}]

    record = await service.apply_migration(db_session, revision="abc", module=None, applied_by="sys")
    assert record.version == "abc"

    rev = await service.get_current_revision(db_session)
    assert rev == "abc"

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.get_pending_migrations")
async def test_apply_migration_duplicate(mock_pending, db_session: AsyncSession):
    db_session.add(MigrationRecord(version="abc", module="mod", description="desc"))
    await db_session.commit()

    mock_pending.return_value = []

    with pytest.raises(DuplicateError):
        await service.apply_migration(db_session, revision="abc", module=None, applied_by="sys")

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.get_pending_migrations")
async def test_apply_migration_not_found(mock_pending, db_session: AsyncSession):
    mock_pending.return_value = [{"revision": "abc", "module": "mod", "description": "desc"}]

    with pytest.raises(NotFoundError):
        await service.apply_migration(db_session, revision="def", module=None, applied_by="sys")

@pytest.mark.asyncio
@patch("src.foundation._009_migration.service.ScriptDirectory")
@patch("src.foundation._009_migration.service.command.downgrade")
@patch("src.foundation._009_migration.service._get_alembic_config")
async def test_rollback_migration_success(mock_cfg, mock_downgrade, mock_script, db_session: AsyncSession):
    db_session.add(MigrationRecord(version="abc", module="mod", description="desc"))
    await db_session.commit()

    mock_rev = MagicMock(down_revision="parent")
    mock_script.from_config.return_value.get_revision.return_value = mock_rev

    record = await service.rollback_migration(db_session, revision="abc", module=None)
    assert record.version == "abc"

    rev = await service.get_current_revision(db_session)
    assert rev is None

@pytest.mark.asyncio
async def test_rollback_migration_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await service.rollback_migration(db_session, revision="abc", module=None)

@pytest.mark.asyncio
async def test_get_migration_history(db_session: AsyncSession):
    db_session.add(MigrationRecord(version="abc", module="mod", description="desc"))
    await db_session.commit()
    history = await service.get_migration_history(db_session)
    assert len(history) == 1
    assert history[0].version == "abc"

@pytest.mark.asyncio
async def test_get_module_status(db_session: AsyncSession):
    db_session.add(MigrationRecord(version="abc", module="mod", description="desc"))
    db_session.add(MigrationRecord(version="def", module="mod", description="desc2"))
    await db_session.commit()

    statuses = await service.get_module_status(db_session)
    assert len(statuses) == 1
    assert statuses[0].module == "mod"
    assert statuses[0].applied_count == 2
    assert statuses[0].current_version == "def"

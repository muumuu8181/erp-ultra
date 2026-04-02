import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from shared.errors import NotFoundError
from src.foundation._006_logging.schemas import LogEntryCreate, LogEntryUpdate
from src.foundation._006_logging import service

@pytest.mark.asyncio
async def test_create_log_entry(db_session: AsyncSession):
    data = LogEntryCreate(level="INFO", message="Test", module="test_module")
    entry = await service.create_log_entry(db_session, data)
    assert entry.id is not None
    assert entry.level == "INFO"
    assert entry.message == "Test"

@pytest.mark.asyncio
async def test_get_log_entry_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await service.get_log_entry(db_session, 999)

@pytest.mark.asyncio
async def test_list_log_entries(db_session: AsyncSession):
    data1 = LogEntryCreate(level="INFO", message="Test 1", module="test_module")
    data2 = LogEntryCreate(level="ERROR", message="Test 2", module="test_module")
    await service.create_log_entry(db_session, data1)
    await service.create_log_entry(db_session, data2)

    items, total = await service.list_log_entries(db_session)
    assert total >= 2
    assert len(items) >= 2

@pytest.mark.asyncio
async def test_update_log_entry(db_session: AsyncSession):
    data = LogEntryCreate(level="INFO", message="Test", module="test_module")
    entry = await service.create_log_entry(db_session, data)

    update_data = LogEntryUpdate(level="DEBUG")
    updated_entry = await service.update_log_entry(db_session, entry.id, update_data)
    assert updated_entry.level == "DEBUG"

@pytest.mark.asyncio
async def test_delete_log_entry(db_session: AsyncSession):
    data = LogEntryCreate(level="INFO", message="Test", module="test_module")
    entry = await service.create_log_entry(db_session, data)

    await service.delete_log_entry(db_session, entry.id)
    with pytest.raises(NotFoundError):
        await service.get_log_entry(db_session, entry.id)

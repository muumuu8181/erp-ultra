import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain._031_audit_log.schemas import AuditLogCreate, AuditLogUpdate
from src.domain._031_audit_log.service import (
    create_audit_log,
    get_audit_log,
    list_audit_logs,
    update_audit_log,
    delete_audit_log,
)
from shared.errors import NotFoundError
from src.foundation._001_database.engine import create_engine, get_session_factory
from shared.types import Base

@pytest.fixture
async def db_session():
    test_engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = get_session_factory(test_engine)
    async with session_factory() as session:
        yield session

@pytest.mark.asyncio
async def test_crud_audit_log(db_session: AsyncSession):
    # Create
    create_data = AuditLogCreate(
        action="CREATE",
        entity_name="Order",
        entity_id="ord_1",
        user_id="user_2"
    )
    audit_log = await create_audit_log(db_session, create_data)
    assert audit_log.id is not None
    assert audit_log.action == "CREATE"

    # Get
    fetched_log = await get_audit_log(db_session, audit_log.id)
    assert fetched_log.id == audit_log.id

    # List
    logs = await list_audit_logs(db_session)
    assert len(logs) >= 1

    # Update
    update_data = AuditLogUpdate(action="UPDATE")
    updated_log = await update_audit_log(db_session, audit_log.id, update_data)
    assert updated_log.action == "UPDATE"

    # Delete
    await delete_audit_log(db_session, audit_log.id)
    with pytest.raises(NotFoundError):
        await get_audit_log(db_session, audit_log.id)

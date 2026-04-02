import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain._031_audit_log.models import AuditLog
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
async def test_audit_log_model(db_session: AsyncSession):
    audit_log = AuditLog(
        action="CREATE",
        entity_name="User",
        entity_id="user_123",
        user_id="admin_1",
        details="User created"
    )
    db_session.add(audit_log)
    await db_session.commit()
    await db_session.refresh(audit_log)

    assert audit_log.id is not None
    assert audit_log.action == "CREATE"
    assert audit_log.entity_name == "User"
    assert audit_log.entity_id == "user_123"
    assert audit_log.user_id == "admin_1"
    assert audit_log.details == "User created"
    assert audit_log.created_at is not None
    assert audit_log.updated_at is not None

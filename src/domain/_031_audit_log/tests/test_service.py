import pytest
from unittest.mock import AsyncMock, MagicMock
from src.domain._031_audit_log.service import create_audit_log, get_audit_logs
from src.domain._031_audit_log.schemas import AuditLogCreate

@pytest.mark.asyncio
async def test_create_audit_log():
    """Test creation of an audit log entry."""
    db_mock = AsyncMock()
    db_mock.add = MagicMock()

    data = AuditLogCreate(
        action="CREATE",
        entity_name="User",
        entity_id="123",
        user_id="admin_1",
        changes={"name": "New User"}
    )

    # Mock behavior of db.refresh
    async def mock_refresh(obj):
        obj.id = 1
        from datetime import datetime, timezone
        obj.created_at = datetime.now(timezone.utc)
        obj.updated_at = datetime.now(timezone.utc)

    db_mock.refresh.side_effect = mock_refresh

    response = await create_audit_log(db_mock, data)

    db_mock.add.assert_called_once()
    db_mock.commit.assert_awaited_once()
    db_mock.refresh.assert_awaited_once()

    assert response.action == "CREATE"
    assert response.entity_name == "User"

@pytest.mark.asyncio
async def test_get_audit_logs():
    """Test retrieving audit logs."""
    db_mock = AsyncMock()

    # Mock total count
    count_result_mock = MagicMock()
    count_result_mock.scalar.return_value = 1

    # Mock data rows
    from datetime import datetime, timezone
    log_mock = MagicMock()
    log_mock.id = 1
    log_mock.created_at = datetime.now(timezone.utc)
    log_mock.updated_at = datetime.now(timezone.utc)
    log_mock.action = "UPDATE"
    log_mock.entity_name = "Product"
    log_mock.entity_id = "456"
    log_mock.user_id = "admin_2"
    log_mock.changes = {"price": 100}

    data_result_mock = MagicMock()
    data_result_mock.scalars().all.return_value = [log_mock]

    # Sequence of returns for execute: first for count, second for data
    db_mock.execute.side_effect = [count_result_mock, data_result_mock]

    response = await get_audit_logs(db_mock, page=1, page_size=10, action="UPDATE")

    assert response.total == 1
    assert len(response.items) == 1
    assert response.items[0].action == "UPDATE"
    assert response.items[0].entity_name == "Product"

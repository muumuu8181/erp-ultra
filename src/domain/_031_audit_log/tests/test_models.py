import pytest
from src.domain._031_audit_log.models import AuditLog

def test_audit_log_initialization():
    """Test that AuditLog can be initialized with correct fields."""
    log = AuditLog(
        action="CREATE",
        entity_name="User",
        entity_id="123",
        user_id="admin_1",
        changes={"name": "New User"}
    )

    assert log.action == "CREATE"
    assert log.entity_name == "User"
    assert log.entity_id == "123"
    assert log.user_id == "admin_1"
    assert log.changes == {"name": "New User"}

import pytest
from src.domain._031_audit_log.schemas import AuditLogCreate
from src.domain._031_audit_log.validators import validate_audit_log_create

def test_validate_audit_log_create_valid():
    """Test valid data passes validation."""
    data = AuditLogCreate(
        action="CREATE",
        entity_name="User",
        entity_id="123",
        user_id="admin_1",
        changes={"name": "New User"}
    )
    validated = validate_audit_log_create(data)
    assert validated == data

def test_validate_audit_log_create_empty_action():
    """Test validation fails for empty action."""
    data = AuditLogCreate(
        action="  ",
        entity_name="User",
        entity_id="123",
        user_id="admin_1",
        changes={"name": "New User"}
    )
    with pytest.raises(ValueError, match="action cannot be empty"):
        validate_audit_log_create(data)

def test_validate_audit_log_create_empty_entity_name():
    """Test validation fails for empty entity_name."""
    data = AuditLogCreate(
        action="CREATE",
        entity_name="",
        entity_id="123",
        user_id="admin_1",
        changes={"name": "New User"}
    )
    with pytest.raises(ValueError, match="entity_name cannot be empty"):
        validate_audit_log_create(data)

def test_validate_audit_log_create_empty_entity_id():
    """Test validation fails for empty entity_id."""
    data = AuditLogCreate(
        action="CREATE",
        entity_name="User",
        entity_id="",
        user_id="admin_1",
        changes={"name": "New User"}
    )
    with pytest.raises(ValueError, match="entity_id cannot be empty"):
        validate_audit_log_create(data)

def test_validate_audit_log_create_empty_user_id():
    """Test validation fails for empty user_id."""
    data = AuditLogCreate(
        action="CREATE",
        entity_name="User",
        entity_id="123",
        user_id=" ",
        changes={"name": "New User"}
    )
    with pytest.raises(ValueError, match="user_id cannot be empty"):
        validate_audit_log_create(data)

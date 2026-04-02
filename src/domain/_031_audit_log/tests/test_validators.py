import pytest
from src.domain._031_audit_log.schemas import AuditLogCreate, AuditLogUpdate
from src.domain._031_audit_log.validators import validate_audit_log_create, validate_audit_log_update
from shared.errors import ValidationError

def test_validate_audit_log_create_valid():
    data = AuditLogCreate(
        action="UPDATE",
        entity_name="Product",
        entity_id="prod_1",
        user_id="user_1"
    )
    # Should not raise
    validate_audit_log_create(data)

def test_validate_audit_log_create_invalid():
    with pytest.raises(ValidationError):
        validate_audit_log_create(AuditLogCreate(
            action="",
            entity_name="Product",
            entity_id="prod_1",
            user_id="user_1"
        ))

def test_validate_audit_log_update_valid():
    data = AuditLogUpdate(action="DELETE")
    # Should not raise
    validate_audit_log_update(data)

def test_validate_audit_log_update_invalid():
    with pytest.raises(ValidationError):
        validate_audit_log_update(AuditLogUpdate(action="  "))

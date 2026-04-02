"""
Validators for the Audit Log module.
"""
from src.domain._031_audit_log.schemas import AuditLogCreate


def validate_audit_log_create(data: AuditLogCreate) -> AuditLogCreate:
    """
    Validates the creation data for an audit log.
    Ensures that required fields are not empty strings.
    """
    if not data.action.strip():
        raise ValueError("action cannot be empty")
    if not data.entity_name.strip():
        raise ValueError("entity_name cannot be empty")
    if not data.entity_id.strip():
        raise ValueError("entity_id cannot be empty")
    if not data.user_id.strip():
        raise ValueError("user_id cannot be empty")
    return data

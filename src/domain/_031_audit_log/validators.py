from shared.errors import ValidationError
from .schemas import AuditLogCreate, AuditLogUpdate

def validate_audit_log_create(data: AuditLogCreate) -> None:
    if not data.action.strip():
        raise ValidationError("Action cannot be empty.")
    if not data.entity_name.strip():
        raise ValidationError("Entity name cannot be empty.")
    if not data.entity_id.strip():
        raise ValidationError("Entity ID cannot be empty.")
    if not data.user_id.strip():
        raise ValidationError("User ID cannot be empty.")

def validate_audit_log_update(data: AuditLogUpdate) -> None:
    if data.action is not None and not data.action.strip():
        raise ValidationError("Action cannot be empty if provided.")
    if data.entity_name is not None and not data.entity_name.strip():
        raise ValidationError("Entity name cannot be empty if provided.")
    if data.entity_id is not None and not data.entity_id.strip():
        raise ValidationError("Entity ID cannot be empty if provided.")
    if data.user_id is not None and not data.user_id.strip():
        raise ValidationError("User ID cannot be empty if provided.")

"""
Pydantic schemas for the Audit Log module.
"""
from datetime import datetime
from typing import Any

from shared.types import BaseSchema


class AuditLogCreate(BaseSchema):
    """Schema for creating a new audit log."""
    action: str
    entity_name: str
    entity_id: str
    user_id: str
    changes: dict[str, Any]


class AuditLogResponse(BaseSchema):
    """Schema for audit log response."""
    id: int
    created_at: datetime
    updated_at: datetime
    action: str
    entity_name: str
    entity_id: str
    user_id: str
    changes: dict[str, Any]

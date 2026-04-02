from typing import Optional
from datetime import datetime

from shared.types import BaseSchema


class AuditLogBase(BaseSchema):
    action: str
    entity_name: str
    entity_id: str
    user_id: str
    details: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogUpdate(BaseSchema):
    action: Optional[str] = None
    entity_name: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    details: Optional[str] = None


class AuditLogResponse(AuditLogBase):
    id: int
    created_at: datetime
    updated_at: datetime

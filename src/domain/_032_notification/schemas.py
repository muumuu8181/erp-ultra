from datetime import datetime
from typing import Optional, Dict
from pydantic import Field, ConfigDict
from shared.types import BaseSchema
from src.domain._032_notification.models import ChannelEnum, StatusEnum, PriorityEnum

class NotificationTemplateCreate(BaseSchema):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    subject: str = Field(..., max_length=500)
    body_template: str
    channel: ChannelEnum
    module: str = Field(..., max_length=50)
    is_active: bool = True

class NotificationTemplateUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=200)
    subject: Optional[str] = Field(None, max_length=500)
    body_template: Optional[str] = None
    channel: Optional[ChannelEnum] = None
    module: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class NotificationTemplateResponse(NotificationTemplateCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NotificationCreate(BaseSchema):
    template_id: Optional[int] = None
    user_id: str
    channel: ChannelEnum
    subject: str = Field(..., max_length=500)
    body: str
    priority: PriorityEnum = PriorityEnum.medium
    scheduled_at: Optional[datetime] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    template_vars: Optional[Dict[str, str]] = None

class NotificationResponse(BaseSchema):
    id: int
    template_id: Optional[int] = None
    user_id: str
    channel: ChannelEnum
    subject: str
    body: str
    status: StatusEnum
    priority: PriorityEnum
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NotificationFilter(BaseSchema):
    user_id: Optional[str] = None
    channel: Optional[ChannelEnum] = None
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    page: int = 1
    size: int = 20

class NotificationStats(BaseSchema):
    total: int
    by_status: dict[str, int]
    by_channel: dict[str, int]
    unread_count: int

class NotificationReadAll(BaseSchema):
    user_id: str

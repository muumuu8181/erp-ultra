from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from shared.types import BaseModel
import enum

class ChannelEnum(str, enum.Enum):
    in_app = "in_app"
    email = "email"
    slack = "slack"

class StatusEnum(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    read = "read"
    failed = "failed"

class PriorityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class NotificationTemplate(BaseModel):
    __tablename__ = "notification_templates"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Notification(BaseModel):
    __tablename__ = "notifications"

    template_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), default=StatusEnum.pending, index=True)
    priority: Mapped[PriorityEnum] = mapped_column(Enum(PriorityEnum), default=PriorityEnum.medium)

    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(nullable=True)

    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_notifications_reference", "reference_type", "reference_id"),
    )

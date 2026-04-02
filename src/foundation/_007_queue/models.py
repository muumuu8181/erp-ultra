from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.schema import ColLen
from shared.types import Base

class MessageStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class QueueMessage(Base):
    __tablename__ = "queue_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    queue_name: Mapped[str] = mapped_column(String(ColLen.SHORT_NAME), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(ColLen.STATUS), nullable=False, default=MessageStatus.PENDING.value, index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    dead_letter: Mapped[Optional["DeadLetterMessage"]] = relationship(back_populates="original_message", uselist=False)

class DeadLetterMessage(Base):
    __tablename__ = "dead_letter_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_message_id: Mapped[int] = mapped_column(Integer, ForeignKey("queue_messages.id"), nullable=False, index=True)
    queue_name: Mapped[str] = mapped_column(String(ColLen.SHORT_NAME), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    failed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    original_message: Mapped["QueueMessage"] = relationship(back_populates="dead_letter")

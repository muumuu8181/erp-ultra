"""
Database models for the event bus.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.schema import ColLen
from shared.types import BaseModel


class EventRecord(BaseModel):
    """Persisted record of every published event for audit trail."""
    __tablename__ = "event_record"

    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Event type in module.action format, e.g. sales_order.created"
    )
    source_module: Mapped[str] = mapped_column(
        String(ColLen.NAME), nullable=False,
        comment="Module that published the event"
    )
    payload: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="Event payload as JSON"
    )
    status: Mapped[str] = mapped_column(
        String(ColLen.STATUS), nullable=False, default="published",
        comment="Event status: published, processed, or failed"
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False,
        comment="When the event was published"
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None,
        comment="When all handlers finished processing"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None,
        comment="Error message if any handler failed"
    )

    def __repr__(self) -> str:
        return f"<EventRecord id={self.id} type={self.event_type} status={self.status}>"


class EventSubscription(BaseModel):
    """Records which handlers are subscribed to which event types."""
    __tablename__ = "event_subscription"

    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Event type pattern to subscribe to (e.g. sales_order.*)"
    )
    handler_module: Mapped[str] = mapped_column(
        String(ColLen.NAME), nullable=False,
        comment="Module that contains the handler"
    )
    handler_function: Mapped[str] = mapped_column(
        String(ColLen.NAME), nullable=False,
        comment="Name of the async handler function"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, nullable=False,
        comment="Whether this subscription is active"
    )

    __table_args__ = (
        UniqueConstraint('event_type', 'handler_module', 'handler_function', name='uq_event_subscription'),
    )

    def __repr__(self) -> str:
        return (
            f"<EventSubscription id={self.id} event={self.event_type} "
            f"handler={self.handler_module}.{self.handler_function}>"
        )

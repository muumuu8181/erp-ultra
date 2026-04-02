"""
Pydantic schemas for the event bus.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from shared.schema import ColLen
from shared.types import BaseSchema


class EventPublish(BaseSchema):
    """Request schema for publishing an event."""
    event_type: str = Field(..., pattern=r"^[a-z_]+\.[a-z_]+$",
        description="Event type in module.action format, e.g. sales_order.created"
    )
    source_module: str = Field(..., max_length=ColLen.NAME,
        description="Module publishing the event"
    )
    payload: dict[str, Any] = Field(default_factory=dict,
        description="Event payload as a JSON-serializable dict"
    )


class EventResponse(BaseSchema):
    """Response schema for a single event."""
    id: int
    event_type: str
    source_module: str
    payload: dict[str, Any]
    status: str
    published_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class EventSubscriptionCreate(BaseSchema):
    """Request schema for creating a subscription."""
    event_type: str = Field(..., description="Event type pattern to subscribe to")
    handler_module: str = Field(..., max_length=ColLen.NAME, description="Module containing the handler")
    handler_function: str = Field(..., max_length=ColLen.NAME, description="Handler function name")


class EventSubscriptionResponse(BaseSchema):
    """Response schema for a subscription."""
    id: int
    event_type: str
    handler_module: str
    handler_function: str
    is_active: bool


class EventFilter(BaseSchema):
    """Filter parameters for querying events."""
    event_type: Optional[str] = None
    source_module: Optional[str] = None
    status: Optional[str] = None
    published_after: Optional[datetime] = None
    published_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)

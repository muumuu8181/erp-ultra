from datetime import datetime

from shared.types import BaseSchema

class QueueMessageCreate(BaseSchema):
    """Schema for creating a queue message."""
    payload: str
    priority: int = 0
    max_retries: int = 3
    scheduled_at: datetime | None = None

class QueueMessageResponse(BaseSchema):
    """Schema for queue message response."""
    id: int
    queue_name: str
    payload: str
    status: str
    priority: int
    retry_count: int
    max_retries: int
    scheduled_at: datetime | None
    processed_at: datetime | None
    created_at: datetime

class DequeueRequest(BaseSchema):
    """Schema for dequeue request (optional)."""
    max_messages: int = 1

class DeadLetterMessageResponse(BaseSchema):
    """Schema for dead letter message response."""
    id: int
    original_message_id: int
    queue_name: str
    payload: str
    error_message: str
    failed_at: datetime

class QueueStats(BaseSchema):
    """Schema for queue statistics."""
    queue_name: str
    pending_count: int
    processing_count: int
    completed_count: int
    failed_count: int
    dead_letter_count: int
    total_count: int

class FailMessageRequest(BaseSchema):
    """Schema for failing a message."""
    error_message: str

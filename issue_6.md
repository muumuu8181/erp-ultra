## Overview

Implement the Async Message Queue module (`_007_queue`) for the ERP system. This module provides an in-memory message queue with database persistence, priority ordering, dead letter handling, and retry logic.

**You MUST follow the exact conventions below. Read every section carefully before writing any code.**

---

## Directory to Create

```
src/foundation/_007_queue/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
├── router.py
├── validators.py
├── README.md
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_service.py
    ├── test_router.py
    └── test_validators.py
```

---

## Import Rules (CRITICAL)

This module is **INDEPENDENT**. Only import from these locations:

```python
# SQLAlchemy base classes
from shared.types import Base, BaseModel

# Pydantic schemas
from shared.types import BaseSchema, PaginatedResponse, AuditableMixin, SoftDeleteMixin

# Custom errors
from shared.errors import NotFoundError, ValidationError, DuplicateError, BusinessRuleError

# Schema constants
from shared.schema import ColLen, Precision

# Database session
from src.foundation._001_database.engine import get_db
```

Do NOT import from any other `_NNN_*` module.

---

## Models (`models.py`)

Use SQLAlchemy 2.0 `Mapped` + `mapped_column` style. All models inherit from `Base` (from `shared.types`).

### Enum for message status:

```python
class MessageStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Table: `queue_messages`

```python
class QueueMessage(Base):
    __tablename__ = "queue_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    queue_name: Mapped[str] = mapped_column(String(ColLen.SHORT_NAME), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    status: Mapped[str] = mapped_column(String(ColLen.STATUS), nullable=False, default=MessageStatus.PENDING, index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    # Relationship
    dead_letter: Mapped[Optional["DeadLetterMessage"]] = relationship(back_populates="original_message", uselist=False)
```

### Table: `dead_letter_messages`

```python
class DeadLetterMessage(Base):
    __tablename__ = "dead_letter_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_message_id: Mapped[int] = mapped_column(Integer, ForeignKey("queue_messages.id"), nullable=False, index=True)
    queue_name: Mapped[str] = mapped_column(String(ColLen.SHORT_NAME), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # Copy of original payload
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    failed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationship
    original_message: Mapped["QueueMessage"] = relationship(back_populates="dead_letter")
```

---

## Schemas (`schemas.py`)

All schemas inherit from `BaseSchema` (from `shared.types`).

```python
class QueueMessageCreate(BaseSchema):
    """Schema for creating a queue message."""
    payload: str  # Must be valid JSON
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
    max_messages: int = 1  # How many messages to dequeue at once

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
```

---

## Validators (`validators.py`)

Each validator function raises `ValidationError` (from `shared.errors`) on failure.

### Functions to implement:

```python
def validate_queue_name(queue_name: str) -> None:
    """
    Validate queue name format.
    Rules: 2-100 characters, lowercase alphanumeric + underscores + hyphens.
    Pattern: r'^[a-z][a-z0-9_-]{1,99}$'
    Raises ValidationError with field="queue_name" if invalid.
    """

def validate_json_payload(payload: str) -> None:
    """
    Validate payload is valid JSON.
    - Parse with json.loads()
    - Raise ValidationError with field="payload" if not valid JSON
    """

def validate_max_retries(max_retries: int) -> None:
    """
    Validate max_retries is reasonable.
    Rules: must be >= 0 and <= 10.
    Raises ValidationError with field="max_retries" if invalid.
    """

def validate_priority(priority: int) -> None:
    """
    Validate priority value.
    Rules: must be >= 0 and <= 100.
    Raises ValidationError with field="priority" if invalid.
    """
```

---

## Service (`service.py`)

All service functions are `async` and accept `db: AsyncSession` as the first parameter. All public functions must have type hints and docstrings.

### In-Memory Queue State:

```python
import asyncio

# Per-queue in-memory queues: {queue_name: asyncio.PriorityQueue}
# PriorityQueue items are tuples of (-priority, created_at, message_id)
# Using negative priority so higher priority = dequeued first
_queue_registry: dict[str, asyncio.PriorityQueue] = {}
```

### Functions to implement:

```python
async def enqueue(db: AsyncSession, queue_name: str, data: QueueMessageCreate) -> QueueMessage:
    """
    Add a message to a queue.
    - Validate queue_name, payload, max_retries, priority
    - Create QueueMessage record with status=pending
    - Add to in-memory priority queue: (-priority, created_at, message_id)
    - If scheduled_at is in the future, do NOT add to in-memory queue yet
      (a background task or the dequeue function will handle scheduled messages)
    - Return created QueueMessage
    """

async def dequeue(db: AsyncSession, queue_name: str, max_messages: int = 1) -> list[QueueMessage]:
    """
    Get the next message(s) from a queue.
    - Get items from in-memory queue (up to max_messages)
    - For each item:
      1. Fetch QueueMessage from DB
      2. Set status to "processing"
      3. If scheduled_at is set and in the future, skip this message
    - Return list of QueueMessage (empty list if queue empty)
    - If in-memory queue is empty, check DB for pending messages not yet in memory
    """

async def complete_message(db: AsyncSession, message_id: int) -> QueueMessage:
    """
    Mark a message as completed.
    - Fetch message by ID (raise NotFoundError if not found)
    - Set status to "completed", processed_at to now
    - Return updated message
    """

async def fail_message(db: AsyncSession, message_id: int, error_message: str) -> QueueMessage:
    """
    Handle a failed message processing.
    - Fetch message by ID (raise NotFoundError if not found)
    - Increment retry_count
    - If retry_count < max_retries:
      - Reset status to "pending"
      - Re-enqueue to in-memory queue
    - Else:
      - Call move_to_dead_letter
    - Return updated message
    """

async def move_to_dead_letter(db: AsyncSession, message_id: int, error_message: str) -> DeadLetterMessage:
    """
    Move a message to the dead letter queue.
    - Fetch message by ID (raise NotFoundError if not found)
    - Set message status to "failed"
    - Create DeadLetterMessage record with:
      - original_message_id = message.id
      - queue_name = message.queue_name
      - payload = message.payload (copy)
      - error_message = error_message
    - Return DeadLetterMessage
    """

async def retry_failed(db: AsyncSession, queue_name: str) -> list[QueueMessage]:
    """
    Retry all failed messages in a queue that haven't exceeded max_retries.
    - Find all messages with status="failed" in the queue
    - For each, reset status to "pending" and retry_count to 0
    - Re-enqueue to in-memory queue
    - Return list of retried messages
    """

async def get_queue_stats(db: AsyncSession, queue_name: str) -> QueueStats:
    """
    Get statistics for a queue.
    - Count messages by status
    - Count dead letter messages
    - Return QueueStats
    """

async def purge_queue(db: AsyncSession, queue_name: str) -> int:
    """
    Remove all pending messages from a queue.
    - Delete all messages with status="pending" for this queue
    - Clear from in-memory queue
    - Return count of purged messages
    """

async def list_dead_letters(db: AsyncSession, queue_name: str | None = None, page: int = 1, page_size: int = 50) -> PaginatedResponse[DeadLetterMessageResponse]:
    """
    List dead letter messages.
    - Optionally filter by queue_name
    - Paginate
    - Return PaginatedResponse
    """

def get_or_create_queue(queue_name: str) -> asyncio.PriorityQueue:
    """
    Get or create the in-memory priority queue for a queue name.
    - If queue_name not in _queue_registry, create new asyncio.PriorityQueue
    - Return the queue
    """

def clear_queue_state() -> None:
    """
    Clear all in-memory queue state.
    Useful for testing.
    """
```

---

## Router (`router.py`)

Router prefix: `/api/v1/queue`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import get_db

router = APIRouter(prefix="/api/v1/queue", tags=["queue"])
```

### Endpoints:

| Method | Path | Description | Request Body / Params | Response |
|--------|------|-------------|----------------------|----------|
| POST | `/queues/{name}/messages` | Enqueue a message | `QueueMessageCreate` | `QueueMessageResponse` |
| POST | `/queues/{name}/dequeue` | Dequeue messages | `DequeueRequest` (optional body) | `list[QueueMessageResponse]` |
| POST | `/messages/{id}/complete` | Complete a message | - | `QueueMessageResponse` |
| POST | `/messages/{id}/fail` | Fail a message | `FailMessageRequest` | `QueueMessageResponse` |
| GET | `/queues/{name}/stats` | Get queue stats | - | `QueueStats` |
| DELETE | `/queues/{name}/purge` | Purge pending messages | - | `{"purged_count": N}` |
| GET | `/dead-letters` | List dead letter messages | Query: queue_name, page, page_size | `PaginatedResponse[DeadLetterMessageResponse]` |

---

## Tests

### `tests/test_models.py`
- Test `QueueMessage` model creation with valid data
- Test `DeadLetterMessage` model creation with valid data
- Test default values (status=pending, priority=0, retry_count=0, max_retries=3)
- Test relationship: QueueMessage -> DeadLetterMessage

### `tests/test_validators.py`
- `test_validate_queue_name_valid`: "orders", "email_notifications", "report-generation"
- `test_validate_queue_name_too_short`: "a" raises ValidationError
- `test_validate_queue_name_uppercase`: "Orders" raises ValidationError
- `test_validate_queue_name_spaces`: "my queue" raises ValidationError
- `test_validate_json_payload_valid`: various valid JSON
- `test_validate_json_payload_invalid`: invalid JSON raises ValidationError
- `test_validate_max_retries_valid`: 0, 1, 3, 10
- `test_validate_max_retries_negative`: raises ValidationError
- `test_validate_max_retries_too_large`: 11 raises ValidationError
- `test_validate_priority_valid`: 0, 1, 50, 100
- `test_validate_priority_negative`: raises ValidationError
- `test_validate_priority_too_large`: 101 raises ValidationError

### `tests/test_service.py`
- Use in-memory SQLite async session.
- `test_enqueue_success`: message created and added to in-memory queue
- `test_enqueue_with_priority`: higher priority messages dequeued first
- `test_enqueue_scheduled`: scheduled messages not immediately available
- `test_dequeue_success`: returns pending message, sets status to processing
- `test_dequeue_empty_queue`: returns empty list
- `test_dequeue_multiple`: dequeues up to max_messages
- `test_dequeue_priority_order`: higher priority dequeued first
- `test_complete_message_success`: sets status to completed
- `test_complete_message_not_found`: raises NotFoundError
- `test_fail_message_retry`: increments retry_count, re-enqueues
- `test_fail_message_exceeds_retries`: moves to dead letter
- `test_move_to_dead_letter`: creates dead letter record
- `test_retry_failed`: resets failed messages and re-enqueues
- `test_get_queue_stats`: returns correct counts
- `test_purge_queue`: removes pending messages
- `test_list_dead_letters`: returns dead letters with pagination
- `test_clear_queue_state`: clears in-memory state

### `tests/test_router.py`
- Use `httpx.AsyncClient` with FastAPI TestClient.
- `test_enqueue_endpoint`: POST /api/v1/queue/queues/orders/messages -> 200
- `test_dequeue_endpoint`: POST /api/v1/queue/queues/orders/dequeue -> 200
- `test_complete_endpoint`: POST /api/v1/queue/messages/{id}/complete -> 200
- `test_fail_endpoint`: POST /api/v1/queue/messages/{id}/fail -> 200
- `test_queue_stats_endpoint`: GET /api/v1/queue/queues/orders/stats -> 200
- `test_purge_endpoint`: DELETE /api/v1/queue/queues/orders/purge -> 200
- `test_dead_letters_endpoint`: GET /api/v1/queue/dead-letters -> 200
- `test_enqueue_invalid_payload`: returns 422

---

## Quality Checklist

- [ ] All files follow the exact directory structure above
- [ ] All imports use only `shared/` and `src.foundation._001_database` -- no other `_NNN_*` imports
- [ ] All models inherit from `Base` (from `shared.types`), NOT from `BaseModel`
- [ ] All schemas inherit from `BaseSchema` (from `shared.types`)
- [ ] All errors raised are from `shared.errors` (NotFoundError, ValidationError, DuplicateError, BusinessRuleError)
- [ ] Column lengths use `ColLen` constants from `shared.schema`
- [ ] Every public function has type hints and a docstring
- [ ] Router prefix is `/api/v1/queue`
- [ ] All tests pass with `pytest -xvs src/foundation/_007_queue/tests/`
- [ ] No hardcoded SQL -- use SQLAlchemy ORM only
- [ ] No synchronous DB calls -- all service functions are `async`
- [ ] `__init__.py` exports router and key service functions
- [ ] In-memory queue uses asyncio.PriorityQueue
- [ ] Priority ordering: higher priority value = processed first
- [ ] Dead letter queue stores copy of original payload
- [ ] Max retries default is 3

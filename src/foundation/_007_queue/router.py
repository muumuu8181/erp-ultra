from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.types import PaginatedResponse
from src.foundation._001_database.engine import get_db
from src.foundation._007_queue.schemas import (
    DeadLetterMessageResponse,
    DequeueRequest,
    FailMessageRequest,
    QueueMessageCreate,
    QueueMessageResponse,
    QueueStats,
)
from src.foundation._007_queue.service import (
    complete_message,
    dequeue,
    enqueue,
    fail_message,
    get_queue_stats,
    list_dead_letters,
    purge_queue,
)

router = APIRouter(prefix="/api/v1/queue", tags=["queue"])

@router.post("/queues/{name}/messages", response_model=QueueMessageResponse)
async def enqueue_endpoint(
    name: str,
    data: QueueMessageCreate,
    db: AsyncSession = Depends(get_db)
) -> QueueMessageResponse:
    """Enqueue a message."""
    message = await enqueue(db, name, data)
    return QueueMessageResponse(
        id=message.id,
        queue_name=message.queue_name,
        payload=message.payload,
        status=message.status,
        priority=message.priority,
        retry_count=message.retry_count,
        max_retries=message.max_retries,
        scheduled_at=message.scheduled_at,
        processed_at=message.processed_at,
        created_at=message.created_at,
    )

@router.post("/queues/{name}/dequeue", response_model=list[QueueMessageResponse])
async def dequeue_endpoint(
    name: str,
    request: DequeueRequest | None = None,
    db: AsyncSession = Depends(get_db)
) -> list[QueueMessageResponse]:
    """Dequeue messages."""
    max_messages = request.max_messages if request else 1
    messages = await dequeue(db, name, max_messages)
    return [
        QueueMessageResponse(
            id=message.id,
            queue_name=message.queue_name,
            payload=message.payload,
            status=message.status,
            priority=message.priority,
            retry_count=message.retry_count,
            max_retries=message.max_retries,
            scheduled_at=message.scheduled_at,
            processed_at=message.processed_at,
            created_at=message.created_at,
        ) for message in messages
    ]

@router.post("/messages/{id}/complete", response_model=QueueMessageResponse)
async def complete_endpoint(
    id: int,
    db: AsyncSession = Depends(get_db)
) -> QueueMessageResponse:
    """Complete a message."""
    message = await complete_message(db, id)
    return QueueMessageResponse(
        id=message.id,
        queue_name=message.queue_name,
        payload=message.payload,
        status=message.status,
        priority=message.priority,
        retry_count=message.retry_count,
        max_retries=message.max_retries,
        scheduled_at=message.scheduled_at,
        processed_at=message.processed_at,
        created_at=message.created_at,
    )

@router.post("/messages/{id}/fail", response_model=QueueMessageResponse)
async def fail_endpoint(
    id: int,
    request: FailMessageRequest,
    db: AsyncSession = Depends(get_db)
) -> QueueMessageResponse:
    """Fail a message."""
    message = await fail_message(db, id, request.error_message)
    return QueueMessageResponse(
        id=message.id,
        queue_name=message.queue_name,
        payload=message.payload,
        status=message.status,
        priority=message.priority,
        retry_count=message.retry_count,
        max_retries=message.max_retries,
        scheduled_at=message.scheduled_at,
        processed_at=message.processed_at,
        created_at=message.created_at,
    )

@router.get("/queues/{name}/stats", response_model=QueueStats)
async def queue_stats_endpoint(
    name: str,
    db: AsyncSession = Depends(get_db)
) -> QueueStats:
    """Get queue stats."""
    return await get_queue_stats(db, name)

@router.delete("/queues/{name}/purge", response_model=dict[str, int])
async def purge_endpoint(
    name: str,
    db: AsyncSession = Depends(get_db)
) -> dict[str, int]:
    """Purge pending messages."""
    purged_count = await purge_queue(db, name)
    return {"purged_count": purged_count}

@router.get("/dead-letters", response_model=PaginatedResponse[DeadLetterMessageResponse])
async def dead_letters_endpoint(
    queue_name: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[DeadLetterMessageResponse]:
    """List dead letter messages."""
    return await list_dead_letters(db, queue_name, page, page_size)

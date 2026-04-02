import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError
from shared.types import PaginatedResponse
from src.foundation._007_queue.models import DeadLetterMessage, MessageStatus, QueueMessage
from src.foundation._007_queue.schemas import (
    DeadLetterMessageResponse,
    QueueMessageCreate,
    QueueStats,
)
from src.foundation._007_queue.validators import (
    validate_json_payload,
    validate_max_retries,
    validate_priority,
    validate_queue_name,
)

_queue_registry: dict[str, asyncio.PriorityQueue] = {}

def get_or_create_queue(queue_name: str) -> asyncio.PriorityQueue:
    """
    Get or create the in-memory priority queue for a queue name.
    """
    if queue_name not in _queue_registry:
        _queue_registry[queue_name] = asyncio.PriorityQueue()
    return _queue_registry[queue_name]

def clear_queue_state() -> None:
    """
    Clear all in-memory queue state.
    """
    _queue_registry.clear()

async def enqueue(db: AsyncSession, queue_name: str, data: QueueMessageCreate) -> QueueMessage:
    """
    Add a message to a queue.
    """
    validate_queue_name(queue_name)
    validate_json_payload(data.payload)
    validate_max_retries(data.max_retries)
    validate_priority(data.priority)

    message = QueueMessage(
        queue_name=queue_name,
        payload=data.payload,
        priority=data.priority,
        max_retries=data.max_retries,
        scheduled_at=data.scheduled_at,
        status=MessageStatus.PENDING,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    if not message.scheduled_at or message.scheduled_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        q = get_or_create_queue(queue_name)
        # Using negative priority so higher priority = dequeued first
        q.put_nowait((-message.priority, message.created_at, message.id))

    return message

async def dequeue(db: AsyncSession, queue_name: str, max_messages: int = 1) -> list[QueueMessage]:
    """
    Get the next message(s) from a queue.
    """
    validate_queue_name(queue_name)
    q = get_or_create_queue(queue_name)

    messages = []

    while len(messages) < max_messages and not q.empty():
        item = q.get_nowait()
        message_id = item[2]

        result = await db.execute(select(QueueMessage).where(QueueMessage.id == message_id))
        msg = result.scalar_one_or_none()

        if not msg:
            continue

        if msg.status != MessageStatus.PENDING:
            continue

        if msg.scheduled_at and msg.scheduled_at > datetime.now(timezone.utc).replace(tzinfo=None):
            # If scheduled in future, skip for now. Note: in a real system we'd re-enqueue it
            # with a delay or have a polling task check the DB. For this spec, we just skip it.
            continue

        msg.status = MessageStatus.PROCESSING
        messages.append(msg)

    # If in-memory queue empty, check DB for pending messages not in memory
    if len(messages) < max_messages:
        # Check DB
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = (
            select(QueueMessage)
            .where(
                QueueMessage.queue_name == queue_name,
                QueueMessage.status == MessageStatus.PENDING,
            )
            .order_by(QueueMessage.priority.desc(), QueueMessage.created_at.asc())
        )
        result = await db.execute(stmt)
        all_pending = result.scalars().all()

        for msg in all_pending:
            if msg.scheduled_at and msg.scheduled_at > now:
                continue

            # Need to make sure it's not already in `messages`
            if any(m.id == msg.id for m in messages):
                continue

            msg.status = MessageStatus.PROCESSING
            messages.append(msg)

            if len(messages) >= max_messages:
                break

    if messages:
        await db.commit()
        for msg in messages:
            await db.refresh(msg)

    return messages

async def complete_message(db: AsyncSession, message_id: int) -> QueueMessage:
    """
    Mark a message as completed.
    """
    result = await db.execute(select(QueueMessage).where(QueueMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("QueueMessage", str(message_id))

    msg.status = MessageStatus.COMPLETED
    msg.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(msg)
    return msg

async def fail_message(db: AsyncSession, message_id: int, error_message: str) -> QueueMessage:
    """
    Handle a failed message processing.
    """
    result = await db.execute(select(QueueMessage).where(QueueMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("QueueMessage", str(message_id))

    msg.retry_count += 1
    if msg.retry_count < msg.max_retries:
        msg.status = MessageStatus.PENDING
        q = get_or_create_queue(msg.queue_name)
        q.put_nowait((-msg.priority, msg.created_at, msg.id))
        await db.commit()
        await db.refresh(msg)
        return msg
    else:
        await db.commit() # Save the retry count bump before moving
        await move_to_dead_letter(db, message_id, error_message)
        await db.refresh(msg)
        return msg

async def move_to_dead_letter(db: AsyncSession, message_id: int, error_message: str) -> DeadLetterMessage:
    """
    Move a message to the dead letter queue.
    """
    result = await db.execute(select(QueueMessage).where(QueueMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("QueueMessage", str(message_id))

    msg.status = MessageStatus.FAILED

    dl_msg = DeadLetterMessage(
        original_message_id=msg.id,
        queue_name=msg.queue_name,
        payload=msg.payload,
        error_message=error_message,
    )
    db.add(dl_msg)
    await db.commit()
    await db.refresh(dl_msg)
    return dl_msg

async def retry_failed(db: AsyncSession, queue_name: str) -> list[QueueMessage]:
    """
    Retry all failed messages in a queue that haven't exceeded max_retries.
    """
    stmt = select(QueueMessage).where(
        QueueMessage.queue_name == queue_name,
        QueueMessage.status == MessageStatus.FAILED
    )
    result = await db.execute(stmt)
    failed_msgs = result.scalars().all()

    retried = []
    q = get_or_create_queue(queue_name)

    for msg in failed_msgs:
        if msg.retry_count < msg.max_retries:
            msg.status = MessageStatus.PENDING
            msg.retry_count = 0
            q.put_nowait((-msg.priority, msg.created_at, msg.id))
            retried.append(msg)

    if retried:
        await db.commit()
        for msg in retried:
            await db.refresh(msg)

    return retried

async def get_queue_stats(db: AsyncSession, queue_name: str) -> QueueStats:
    """
    Get statistics for a queue.
    """
    stmt = select(QueueMessage.status, func.count()).where(QueueMessage.queue_name == queue_name).group_by(QueueMessage.status)
    result = await db.execute(stmt)
    counts = dict(result.all())

    dl_stmt = select(func.count()).where(DeadLetterMessage.queue_name == queue_name)
    dl_result = await db.execute(dl_stmt)
    dl_count = dl_result.scalar() or 0

    pending = counts.get(MessageStatus.PENDING, 0)
    processing = counts.get(MessageStatus.PROCESSING, 0)
    completed = counts.get(MessageStatus.COMPLETED, 0)
    failed = counts.get(MessageStatus.FAILED, 0)
    total = pending + processing + completed + failed

    return QueueStats(
        queue_name=queue_name,
        pending_count=pending,
        processing_count=processing,
        completed_count=completed,
        failed_count=failed,
        dead_letter_count=dl_count,
        total_count=total,
    )

async def purge_queue(db: AsyncSession, queue_name: str) -> int:
    """
    Remove all pending messages from a queue.
    """
    stmt = delete(QueueMessage).where(
        QueueMessage.queue_name == queue_name,
        QueueMessage.status == MessageStatus.PENDING
    )
    result = await db.execute(stmt)
    await db.commit()

    # Clear from in-memory queue
    if queue_name in _queue_registry:
        q = _queue_registry[queue_name]
        while not q.empty():
            q.get_nowait()

    return result.rowcount

async def list_dead_letters(db: AsyncSession, queue_name: str | None = None, page: int = 1, page_size: int = 50) -> PaginatedResponse[DeadLetterMessageResponse]:
    """
    List dead letter messages.
    """
    stmt = select(DeadLetterMessage)
    if queue_name:
        stmt = stmt.where(DeadLetterMessage.queue_name == queue_name)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Paginate
    stmt = stmt.order_by(DeadLetterMessage.failed_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    items_response = [
        DeadLetterMessageResponse(
            id=item.id,
            original_message_id=item.original_message_id,
            queue_name=item.queue_name,
            payload=item.payload,
            error_message=item.error_message,
            failed_at=item.failed_at,
        ) for item in items
    ]

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=items_response,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

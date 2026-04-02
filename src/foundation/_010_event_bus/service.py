"""
Event Bus service implementation.
"""
import asyncio
import logging
from typing import Callable, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError
from shared.interfaces import Event, EventBus
from src.foundation._010_event_bus.models import EventRecord, EventSubscription
from src.foundation._010_event_bus.schemas import EventFilter
from src.foundation._010_event_bus.validators import (
    validate_event_type_format,
    validate_handler_module_exists,
    validate_subscription_not_duplicate,
)

logger = logging.getLogger(__name__)

# Module-level registry: maps event_type patterns to list of handler callables
_subscribers: dict[str, list[Callable]] = {}


async def _dispatch_to_handlers(event: Event, handlers: list[Callable]) -> list[Exception | None]:
    """Dispatch event to all handlers with error isolation.

    Each handler runs independently. A failure in one handler does NOT
    prevent other handlers from executing.

    Args:
        event: The Event to dispatch.
        handlers: List of async callables.
    Returns:
        List of results - None for success, Exception for failure.
    """
    results = await asyncio.gather(
        *[handler(event) for handler in handlers],
        return_exceptions=True
    )
    return list(results)


def _get_matching_handlers(event_type: str) -> list[Callable]:
    """Get all handlers registered for this event type."""
    handlers = []
    # Match specific
    if event_type in _subscribers:
        handlers.extend(_subscribers[event_type])

    # Match wildcard module.*
    module = event_type.split('.')[0]
    module_wildcard = f"{module}.*"
    if module_wildcard in _subscribers:
        handlers.extend(_subscribers[module_wildcard])

    # Match global wildcard *
    if "*" in _subscribers:
        handlers.extend(_subscribers["*"])

    return handlers


async def publish_event(db: AsyncSession, event_type: str, source_module: str, payload: dict) -> EventRecord:
    """Publish an event to all subscribers and persist to DB."""
    record = EventRecord(
        event_type=event_type,
        source_module=source_module,
        payload=payload,
        status="published"
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    event = Event(event_type=event_type, module=source_module, data=payload)
    handlers = _get_matching_handlers(event_type)

    if handlers:
        results = await _dispatch_to_handlers(event, handlers)

        has_error = False
        error_msgs = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                has_error = True
                error_msgs.append(f"Handler {i} failed: {str(result)}")

        if has_error:
            record.status = "failed"
            record.error_message = "; ".join(error_msgs)
        else:
            record.status = "processed"

        record.processed_at = func.now()
        await db.commit()
        await db.refresh(record)
    else:
        record.status = "processed"
        record.processed_at = func.now()
        await db.commit()
        await db.refresh(record)

    return record


async def subscribe_handler(
    db: AsyncSession, event_type: str, handler_module: str, handler_function: str
) -> EventSubscription:
    """Register a handler for an event type."""
    validate_event_type_format(event_type)
    await validate_handler_module_exists(db, handler_module)

    # Check for duplicate
    result = await db.execute(
        select(EventSubscription).where(
            EventSubscription.event_type == event_type,
            EventSubscription.handler_module == handler_module,
            EventSubscription.handler_function == handler_function
        )
    )
    existing = list(result.scalars().all())
    validate_subscription_not_duplicate(event_type, handler_module, handler_function, existing)

    # Check if we have an inactive one we can reactive
    subscription = None
    for sub in existing:
        if not sub.is_active:
            sub.is_active = True
            subscription = sub
            break

    if not subscription:
        subscription = EventSubscription(
            event_type=event_type,
            handler_module=handler_module,
            handler_function=handler_function,
            is_active=True
        )
        db.add(subscription)

    await db.commit()
    await db.refresh(subscription)
    return subscription


async def unsubscribe_handler(db: AsyncSession, subscription_id: int) -> None:
    """Deactivate a subscription by ID."""
    result = await db.execute(select(EventSubscription).where(EventSubscription.id == subscription_id))
    subscription = result.scalars().first()
    if not subscription:
        raise NotFoundError("EventSubscription", str(subscription_id))

    subscription.is_active = False
    await db.commit()


async def replay_event(db: AsyncSession, event_id: int) -> EventRecord:
    """Re-publish a previously recorded event."""
    result = await db.execute(select(EventRecord).where(EventRecord.id == event_id))
    record = result.scalars().first()
    if not record:
        raise NotFoundError("EventRecord", str(event_id))

    return await publish_event(
        db, record.event_type, record.source_module, record.payload
    )


async def get_event_history(db: AsyncSession, filters: EventFilter) -> tuple[list[EventRecord], int]:
    """Query event history with filters and pagination."""
    query = select(EventRecord)

    if filters.event_type:
        query = query.where(EventRecord.event_type == filters.event_type)
    if filters.source_module:
        query = query.where(EventRecord.source_module == filters.source_module)
    if filters.status:
        query = query.where(EventRecord.status == filters.status)
    if filters.published_after:
        query = query.where(EventRecord.published_at >= filters.published_after)
    if filters.published_before:
        query = query.where(EventRecord.published_at <= filters.published_before)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(EventRecord.published_at.desc())
    query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def get_subscriptions(db: AsyncSession, event_type: Optional[str] = None) -> list[EventSubscription]:
    """List all active subscriptions, optionally filtered by event_type."""
    query = select(EventSubscription).where(EventSubscription.is_active.is_(True))
    if event_type:
        query = query.where(EventSubscription.event_type == event_type)

    result = await db.execute(query)
    return list(result.scalars().all())


class DatabaseEventBus(EventBus):
    """Database-backed EventBus implementation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        await publish_event(self.db, event.event_type, event.module, event.data)

    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe a callable to an event type. Memory only in this interface method."""
        if event_type not in _subscribers:
            _subscribers[event_type] = []
        if handler not in _subscribers[event_type]:
            _subscribers[event_type].append(handler)

    async def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe a callable from an event type."""
        if event_type in _subscribers and handler in _subscribers[event_type]:
            _subscribers[event_type].remove(handler)

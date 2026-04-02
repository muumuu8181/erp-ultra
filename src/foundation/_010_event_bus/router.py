"""
Event Bus router.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.types import PaginatedResponse
from src.foundation._001_database.engine import get_db
from src.foundation._010_event_bus import service
from src.foundation._010_event_bus.schemas import (
    EventFilter,
    EventPublish,
    EventResponse,
    EventSubscriptionCreate,
    EventSubscriptionResponse,
)

router = APIRouter(prefix="/api/v1/events", tags=["event-bus"])


@router.post("/publish", response_model=EventResponse, status_code=201)
async def publish_event(
    event: EventPublish,
    db: AsyncSession = Depends(get_db)
):
    """Publish a new event to the bus."""
    record = await service.publish_event(
        db,
        event_type=event.event_type,
        source_module=event.source_module,
        payload=event.payload
    )
    return record


@router.get("", response_model=PaginatedResponse[EventResponse])
async def list_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    source_module: Optional[str] = Query(None, description="Filter by source module"),
    status: Optional[str] = Query(None, description="Filter by status (published/processed/failed)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """List event history with optional filters and pagination."""
    filters = EventFilter(
        event_type=event_type,
        source_module=source_module,
        status=status,
        page=page,
        page_size=page_size
    )
    items, total = await service.get_event_history(db, filters)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/subscriptions", response_model=list[EventSubscriptionResponse])
async def list_subscriptions(
    event_type: Optional[str] = Query(None, description="Filter by event type pattern"),
    db: AsyncSession = Depends(get_db)
):
    """List all active event subscriptions."""
    return await service.get_subscriptions(db, event_type)


@router.post("/subscriptions", response_model=EventSubscriptionResponse, status_code=201)
async def create_subscription(
    sub: EventSubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new event subscription."""
    return await service.subscribe_handler(
        db,
        event_type=sub.event_type,
        handler_module=sub.handler_module,
        handler_function=sub.handler_function
    )


@router.get("/{id}", response_model=EventResponse)
async def get_event(id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific event by ID."""
    # We can reuse get_event_history to avoid direct db queries here,
    # but a simple select is better. The service doesn't have a get_event_by_id,
    # but it's simple enough.
    from sqlalchemy import select

    from shared.errors import NotFoundError
    from src.foundation._010_event_bus.models import EventRecord

    result = await db.execute(select(EventRecord).where(EventRecord.id == id))
    record = result.scalars().first()
    if not record:
        raise NotFoundError("EventRecord", str(id))
    return record


@router.post("/{id}/replay", response_model=EventResponse)
async def replay_event(id: int, db: AsyncSession = Depends(get_db)):
    """Replay a previously published event."""
    return await service.replay_event(db, id)

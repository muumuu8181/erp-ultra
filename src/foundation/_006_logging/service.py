from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.errors import NotFoundError
from .models import LogEntry
from .schemas import LogEntryCreate, LogEntryUpdate

async def create_log_entry(db: AsyncSession, data: LogEntryCreate) -> LogEntry:
    """Create a new log entry in the database."""
    log_entry = LogEntry(**data.model_dump())
    db.add(log_entry)
    await db.flush()
    return log_entry

async def get_log_entry(db: AsyncSession, id: int) -> LogEntry:
    """Retrieve a log entry by ID."""
    result = await db.execute(select(LogEntry).where(LogEntry.id == id))
    log_entry = result.scalar_one_or_none()
    if not log_entry:
        raise NotFoundError(resource="LogEntry", resource_id=str(id))
    return log_entry

async def list_log_entries(
    db: AsyncSession, skip: int = 0, limit: int = 50
) -> tuple[List[LogEntry], int]:
    """List log entries with pagination."""
    # Count total
    total_result = await db.execute(select(func.count(LogEntry.id)))
    total = total_result.scalar_one()

    # Get items
    result = await db.execute(
        select(LogEntry).order_by(LogEntry.created_at.desc()).offset(skip).limit(limit)
    )
    items = list(result.scalars().all())

    return items, total

async def update_log_entry(db: AsyncSession, id: int, data: LogEntryUpdate) -> LogEntry:
    """Update a log entry."""
    log_entry = await get_log_entry(db, id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(log_entry, key, value)
    await db.flush()
    await db.refresh(log_entry)
    return log_entry

async def delete_log_entry(db: AsyncSession, id: int) -> bool:
    """Delete a log entry."""
    log_entry = await get_log_entry(db, id)
    await db.delete(log_entry)
    await db.flush()
    return True

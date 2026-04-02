from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from shared.types import PaginatedResponse
from src.foundation._001_database import get_db

from .schemas import LogEntryCreate, LogEntryUpdate, LogEntryResponse
from . import service
from .validators import validate_log_entry_create

router = APIRouter(prefix="/api/v1/logging", tags=["logging"])

@router.post("/", response_model=LogEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_log(
    data: LogEntryCreate, db: AsyncSession = Depends(get_db)
) -> LogEntryResponse:
    """Create a new log entry."""
    validate_log_entry_create(data)
    entry = await service.create_log_entry(db, data)
    return LogEntryResponse.model_validate(entry)

@router.get("/", response_model=PaginatedResponse[LogEntryResponse])
async def list_logs(
    skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[LogEntryResponse]:
    """List log entries with pagination."""
    items, total = await service.list_log_entries(db, skip=skip, limit=limit)
    response_items = [LogEntryResponse.model_validate(item) for item in items]

    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1

    return PaginatedResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )

@router.get("/{id}", response_model=LogEntryResponse)
async def get_log(id: int, db: AsyncSession = Depends(get_db)) -> LogEntryResponse:
    """Get a log entry by ID."""
    entry = await service.get_log_entry(db, id)
    return LogEntryResponse.model_validate(entry)

@router.put("/{id}", response_model=LogEntryResponse)
async def update_log(
    id: int, data: LogEntryUpdate, db: AsyncSession = Depends(get_db)
) -> LogEntryResponse:
    """Update a log entry."""
    # We do not validate level here explicitly unless it is provided
    if data.level is not None:
        from .validators import validate_log_level
        validate_log_level(data.level)

    entry = await service.update_log_entry(db, id, data)
    return LogEntryResponse.model_validate(entry)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a log entry."""
    await service.delete_log_entry(db, id)

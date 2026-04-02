"""
HTTP API router for the _009_migration module.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from src.foundation._009_migration import service, validators
from src.foundation._009_migration.schemas import (
    MigrationStatusResponse,
    MigrationApplyRequest,
    MigrationRollbackRequest,
    MigrationHistoryEntry,
)

router = APIRouter(prefix="/api/v1/migrations", tags=["migrations"])


@router.get("/status", response_model=MigrationStatusResponse)
async def get_status(db: AsyncSession = Depends(get_db)) -> MigrationStatusResponse:
    """Get overall migration status."""
    current_revision = await service.get_current_revision(db)
    pending = await service.get_pending_migrations(db)
    modules = await service.get_module_status(db)

    return MigrationStatusResponse(
        current_revision=current_revision,
        is_up_to_date=len(pending) == 0,
        pending_count=len(pending),
        modules=modules,
    )


@router.get("/pending", response_model=list[dict[str, str]])
async def list_pending(db: AsyncSession = Depends(get_db)) -> list[dict[str, str]]:
    """List pending migrations."""
    return await service.get_pending_migrations(db)


@router.post("/apply", response_model=MigrationHistoryEntry)
async def apply_migration(
    request: MigrationApplyRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    """Apply one or more migrations."""
    if request.revision:
        validators.validate_revision_format(request.revision)
        await validators.validate_migration_not_applied(db, request.revision)
    if request.module:
        validators.validate_module_name(request.module)

    record = await service.apply_migration(
        db, revision=request.revision, module=request.module, applied_by=request.applied_by
    )

    return record


@router.post("/rollback", response_model=MigrationHistoryEntry)
async def rollback_migration(
    request: MigrationRollbackRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    """Rollback to a specific revision."""
    validators.validate_revision_format(request.revision)
    if request.module:
        validators.validate_module_name(request.module)

    record = await service.rollback_migration(
        db, revision=request.revision, module=request.module
    )

    return record


@router.get("/history", response_model=list[MigrationHistoryEntry])
async def get_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get migration history."""
    return await service.get_migration_history(db, limit=limit, offset=offset)

from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from shared.errors import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database import get_db
from .schemas import AuditLogCreate, AuditLogUpdate, AuditLogResponse
from .service import (
    create_audit_log,
    get_audit_log,
    list_audit_logs,
    update_audit_log,
    delete_audit_log,
)

router = APIRouter(prefix="/api/v1/audit-log", tags=["Audit Log"])


@router.post("/", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_log_endpoint(
    data: AuditLogCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new audit log entry."""
    return await create_audit_log(db, data)


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log_endpoint(
    audit_log_id: int, db: AsyncSession = Depends(get_db)
):
    """Get an audit log entry by ID."""
    try:
        return await get_audit_log(db, audit_log_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs_endpoint(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """List all audit log entries."""
    return await list_audit_logs(db, skip=skip, limit=limit)


@router.put("/{audit_log_id}", response_model=AuditLogResponse)
async def update_audit_log_endpoint(
    audit_log_id: int, data: AuditLogUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an audit log entry."""
    try:
        return await update_audit_log(db, audit_log_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{audit_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit_log_endpoint(
    audit_log_id: int, db: AsyncSession = Depends(get_db)
):
    """Delete an audit log entry."""
    try:
        await delete_audit_log(db, audit_log_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

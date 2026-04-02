"""
FastAPI router for the Audit Log module.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.types import PaginatedResponse
from src.foundation._001_database import get_db
from src.domain._031_audit_log.schemas import AuditLogCreate, AuditLogResponse
from src.domain._031_audit_log.service import create_audit_log, get_audit_logs

router = APIRouter(
    prefix="/api/v1/audit-log",
    tags=["Audit Log"]
)

@router.post("", response_model=AuditLogResponse, status_code=201)
async def create_audit_log_endpoint(
    data: AuditLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new audit log.
    """
    try:
        return await create_audit_log(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def get_audit_logs_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    action: Optional[str] = None,
    entity_name: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated audit logs, optionally filtered.
    """
    return await get_audit_logs(
        db=db,
        page=page,
        page_size=page_size,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        user_id=user_id
    )

"""
Service layer for the Audit Log module.
"""
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared.types import PaginatedResponse
from src.domain._031_audit_log.models import AuditLog
from src.domain._031_audit_log.schemas import AuditLogCreate, AuditLogResponse
from src.domain._031_audit_log.validators import validate_audit_log_create


async def create_audit_log(db: AsyncSession, data: AuditLogCreate) -> AuditLogResponse:
    """
    Creates a new audit log entry.
    """
    validate_audit_log_create(data)

    audit_log = AuditLog(
        action=data.action,
        entity_name=data.entity_name,
        entity_id=data.entity_id,
        user_id=data.user_id,
        changes=data.changes
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)

    return AuditLogResponse.model_validate(audit_log)


async def get_audit_logs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = None,
    entity_name: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> PaginatedResponse[AuditLogResponse]:
    """
    Retrieves a paginated list of audit logs, optionally filtered.
    """
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if entity_name:
        query = query.where(AuditLog.entity_name == entity_name)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    items = [AuditLogResponse.model_validate(log) for log in logs]
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

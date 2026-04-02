from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import NotFoundError
from .models import AuditLog
from .schemas import AuditLogCreate, AuditLogUpdate
from .validators import validate_audit_log_create, validate_audit_log_update


async def create_audit_log(db: AsyncSession, data: AuditLogCreate) -> AuditLog:
    """Create a new audit log."""
    validate_audit_log_create(data)

    audit_log = AuditLog(**data.model_dump())
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    return audit_log


async def get_audit_log(db: AsyncSession, audit_log_id: int) -> AuditLog:
    """Get an audit log by ID."""
    query = select(AuditLog).where(AuditLog.id == audit_log_id)
    result = await db.execute(query)
    audit_log = result.scalar_one_or_none()

    if not audit_log:
        raise NotFoundError(f"Audit log with ID {audit_log_id} not found")

    return audit_log


async def list_audit_logs(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[AuditLog]:
    """List all audit logs with pagination."""
    query = select(AuditLog).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_audit_log(
    db: AsyncSession, audit_log_id: int, data: AuditLogUpdate
) -> AuditLog:
    """Update an existing audit log."""
    validate_audit_log_update(data)

    audit_log = await get_audit_log(db, audit_log_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(audit_log, key, value)

    await db.commit()
    await db.refresh(audit_log)
    return audit_log


async def delete_audit_log(db: AsyncSession, audit_log_id: int) -> None:
    """Delete an audit log by ID."""
    audit_log = await get_audit_log(db, audit_log_id)
    await db.delete(audit_log)
    await db.commit()

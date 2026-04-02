"""
Service layer for database migrations.
"""
import re
from datetime import datetime
from typing import Optional

import asyncio
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from shared.errors import NotFoundError, DuplicateError, BusinessRuleError
from src.foundation._009_migration.models import MigrationRecord
from src.foundation._009_migration.schemas import MigrationModuleStatus

def _get_alembic_config() -> Config:
    """Helper to get Alembic config."""
    alembic_cfg = Config("alembic.ini")
    return alembic_cfg

async def get_current_revision(db: AsyncSession) -> Optional[str]:
    """Return the current head revision from the migration_record table.

    Args:
        db: AsyncSession for database access.
    Returns:
        The version string of the most recently applied migration, or None if none applied.
    """
    stmt = select(MigrationRecord.version).order_by(desc(MigrationRecord.applied_at), desc(MigrationRecord.id)).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_pending_migrations(db: AsyncSession) -> list[dict[str, str]]:
    """List migrations that have not yet been applied.

    Reads the Alembic migration directory and compares against applied MigrationRecords.

    Args:
        db: AsyncSession for database access.
    Returns:
        List of dicts with keys: revision, module, description.
    """
    # Get all applied revisions
    stmt = select(MigrationRecord.version)
    result = await db.execute(stmt)
    applied_versions = {row for row in result.scalars()}

    alembic_cfg = _get_alembic_config()
    script = ScriptDirectory.from_config(alembic_cfg)

    pending = []
    # walk_revisions returns revisions from head down to base.
    # We want pending ones.
    for rev in script.walk_revisions():
        if rev.revision not in applied_versions:
            # Parse module from docstring: "[_009_migration] Some description"
            doc = rev.doc or ""
            module_name = "unknown"
            description = doc
            match = re.match(r"^\[(.*?)\]\s*(.*)$", doc)
            if match:
                module_name = match.group(1)
                description = match.group(2)

            pending.append({
                "revision": rev.revision,
                "module": module_name,
                "description": description
            })

    # Return in chronological order (oldest to newest)
    return list(reversed(pending))

async def apply_migration(db: AsyncSession, revision: Optional[str], module: Optional[str], applied_by: str) -> MigrationRecord:
    """Apply a migration (or all pending if revision is None).

    Args:
        db: AsyncSession for database access.
        revision: Specific revision hash to apply. If None, applies all pending.
        module: If provided, only apply migrations belonging to this module.
        applied_by: Identifier of who is applying the migration.
    Returns:
        The MigrationRecord for the applied migration.
    Raises:
        NotFoundError: If specified revision does not exist.
        DuplicateError: If the migration has already been applied.
        BusinessRuleError: If applying migrations out of order.
    """
    pending = await get_pending_migrations(db)

    target_rev = None
    target_info = None

    if revision:
        # Check if it's already applied
        stmt = select(MigrationRecord).where(MigrationRecord.version == revision)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise DuplicateError("Migration", revision)

        if not pending:
            raise BusinessRuleError("No pending migrations to apply")

        # Find in pending
        for i, p in enumerate(pending):
            if p["revision"] == revision:
                if i > 0:
                    raise BusinessRuleError("Cannot apply migrations out of order")
                target_rev = revision
                target_info = p
                break

        if not target_rev:
            raise NotFoundError("Migration revision", revision)
    else:
        if not pending:
            raise BusinessRuleError("No pending migrations to apply")

        # Apply all pending migrations sequentially
        # If module is provided, we only apply migrations for that module
        alembic_cfg = _get_alembic_config()
        last_record = None

        for target_info in pending:
            if module and target_info["module"] != module:
                # If module is specified, we skip migrations that don't match or maybe error out?
                # The issue says "If provided, only apply migrations belonging to this module."
                continue

            target_rev = target_info["revision"]

            await asyncio.to_thread(command.upgrade, alembic_cfg, target_rev)

            # Insert record
            record = MigrationRecord(
                version=target_rev,
                module=target_info["module"],
                description=target_info["description"],
                applied_by=applied_by
            )
            db.add(record)
            await db.flush()
            last_record = record

        if not last_record:
            raise BusinessRuleError("No pending migrations matched the specified criteria to apply")

        return last_record

    alembic_cfg = _get_alembic_config()
    await asyncio.to_thread(command.upgrade, alembic_cfg, target_rev)

    # Insert record
    record = MigrationRecord(
        version=target_rev,
        module=target_info["module"],
        description=target_info["description"],
        applied_by=applied_by
    )
    db.add(record)
    await db.flush()
    return record

async def rollback_migration(db: AsyncSession, revision: str, module: Optional[str]) -> MigrationRecord:
    """Rollback to a specific revision.

    Removes the MigrationRecord for the given revision. The actual schema rollback
    is handled by Alembic downgrade.

    Args:
        db: AsyncSession for database access.
        revision: Target revision to rollback to.
        module: If provided, restrict rollback to this module.
    Returns:
        The MigrationRecord that was removed.
    Raises:
        NotFoundError: If the specified revision is not found in applied migrations.
        BusinessRuleError: If rollback would break dependencies.
    """
    stmt = select(MigrationRecord).order_by(desc(MigrationRecord.applied_at), desc(MigrationRecord.id)).limit(1)
    result = await db.execute(stmt)
    latest = result.scalar_one_or_none()

    if not latest:
        raise NotFoundError("Migration revision", revision)

    if latest.version != revision:
        raise BusinessRuleError("Can only rollback the most recently applied migration")

    if module and latest.module != module:
        raise BusinessRuleError("Latest migration does not belong to specified module")

    # Get the parent revision to downgrade TO
    alembic_cfg = _get_alembic_config()
    script = ScriptDirectory.from_config(alembic_cfg)
    rev_obj = script.get_revision(revision)
    if not rev_obj:
        raise NotFoundError("Migration revision in Alembic script directory", revision)

    # We downgrade to the parent revision (or base if no parent)
    downgrade_target = rev_obj.down_revision or "-1"

    await asyncio.to_thread(command.downgrade, alembic_cfg, str(downgrade_target))

    await db.delete(latest)
    await db.flush()
    return latest

async def get_migration_history(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[MigrationRecord]:
    """Return migration history ordered by applied_at descending.

    Args:
        db: AsyncSession for database access.
        limit: Maximum number of records to return.
        offset: Number of records to skip.
    Returns:
        List of MigrationRecord objects.
    """
    stmt = select(MigrationRecord).order_by(desc(MigrationRecord.applied_at), desc(MigrationRecord.id)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars())

async def get_module_status(db: AsyncSession) -> list[MigrationModuleStatus]:
    """Get migration status grouped by module.

    Args:
        db: AsyncSession for database access.
    Returns:
        List of MigrationModuleStatus, one per module that has migrations.
    """
    stmt = select(
        MigrationRecord.module,
        func.count(MigrationRecord.id).label("applied_count"),
        func.max(MigrationRecord.applied_at).label("last_applied_at")
    ).group_by(MigrationRecord.module)

    stats_result = await db.execute(stmt)

    statuses = []
    for row in stats_result.all():
        module_name = row.module

        # Get latest record for this module to get version and description
        latest_stmt = select(MigrationRecord).where(MigrationRecord.module == module_name).order_by(desc(MigrationRecord.applied_at), desc(MigrationRecord.id)).limit(1)
        latest_result = await db.execute(latest_stmt)
        latest_record = latest_result.scalar_one_or_none()

        statuses.append(MigrationModuleStatus(
            module=module_name,
            current_version=latest_record.version if latest_record else None,
            current_description=latest_record.description if latest_record else None,
            applied_count=row.applied_count,
            last_applied_at=row.last_applied_at
        ))

    return statuses

async def generate_migration_stamp(module: str, description: str) -> str:
    """Generate a stamped migration file for a given module.

    Creates an Alembic migration file with proper module tagging in the
    revision description. The migration file is placed in the Alembic
    migrations directory.

    Args:
        module: The module directory name (e.g. "_009_migration").
        description: Human-readable description of the migration.
    Returns:
        The generated revision hash string.
    """
    alembic_cfg = _get_alembic_config()
    message = f"[{module}] {description}"

    # command.revision generates a new revision file
    rev = await asyncio.to_thread(command.revision, alembic_cfg, message=message, autogenerate=False)

    return rev.revision if rev else ""

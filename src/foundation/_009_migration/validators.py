"""
Validation logic for migrations.
"""
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError, DuplicateError
from src.foundation._009_migration.models import MigrationRecord


def validate_revision_format(revision: str) -> str:
    """Validate that a revision string is a valid format (alphanumeric, 12 chars hex).

    Args:
        revision: The revision hash to validate.
    Returns:
        The validated revision string.
    Raises:
        ValidationError: If the revision format is invalid.
    """
    if not re.match(r"^[a-fA-F0-9]{12}$", revision):
        raise ValidationError("Invalid revision format. Must be 12-character hex string.", field="revision")
    return revision


async def validate_migration_not_applied(db: AsyncSession, revision: str) -> None:
    """Ensure the given migration revision has not already been applied.

    Args:
        db: AsyncSession for database access.
        revision: The revision hash to check.
    Raises:
        DuplicateError: If the migration has already been applied.
    """
    stmt = select(MigrationRecord).where(MigrationRecord.version == revision)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise DuplicateError("Migration", revision)


def validate_module_name(module: str) -> str:
    """Validate that a module name follows the pattern _NNN_name.

    Args:
        module: Module directory name.
    Returns:
        The validated module name.
    Raises:
        ValidationError: If the format is invalid.
    """
    if not re.match(r"^_[0-9]{3}_[a-zA-Z0-9_]+$", module):
        raise ValidationError("Invalid module name format. Must follow _NNN_name pattern.", field="module")
    return module

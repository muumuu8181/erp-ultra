"""
Pydantic schemas for the _009_migration module.
"""
from datetime import datetime
from typing import Optional
from pydantic import Field, ConfigDict

from shared.types import BaseSchema
from shared.schema import ColLen


class MigrationModuleStatus(BaseSchema):
    """Status of migrations for a single module."""
    model_config = ConfigDict(from_attributes=True)

    module: str = Field(..., description="Module directory name (e.g. _009_migration)")
    current_version: Optional[str] = Field(None, description="Current applied revision hash")
    current_description: Optional[str] = Field(None, description="Description of current revision")
    applied_count: int = Field(0, description="Number of migrations applied for this module")
    last_applied_at: Optional[datetime] = Field(None, description="Timestamp of most recent applied migration")


class MigrationStatusResponse(BaseSchema):
    """Overall migration status across all modules."""
    model_config = ConfigDict(from_attributes=True)

    current_revision: Optional[str] = Field(None, description="Current Alembic head revision")
    is_up_to_date: bool = Field(False, description="True if no pending migrations")
    pending_count: int = Field(0, description="Number of pending migrations")
    modules: list[MigrationModuleStatus] = Field(default_factory=list, description="Per-module status breakdown")


class MigrationApplyRequest(BaseSchema):
    """Request to apply a migration."""
    model_config = ConfigDict(from_attributes=True)

    revision: Optional[str] = Field(None, description="Specific revision to apply. If None, applies all pending.")
    module: Optional[str] = Field(None, description="Restrict to a specific module.")
    applied_by: str = Field("system", max_length=ColLen.SHORT_NAME)


class MigrationRollbackRequest(BaseSchema):
    """Request to rollback a migration."""
    model_config = ConfigDict(from_attributes=True)

    revision: str = Field(..., description="Revision to rollback to")
    module: Optional[str] = Field(None, description="Restrict to a specific module.")
    rolled_back_by: str = Field("system", max_length=ColLen.SHORT_NAME)


class MigrationHistoryEntry(BaseSchema):
    """A single entry in migration history."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: str
    module: str
    description: str
    applied_at: datetime
    applied_by: str

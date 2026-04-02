"""
Database models for the _009_migration module.
"""
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel
from shared.schema import ColLen


class MigrationRecord(BaseModel):
    """Tracks applied database migrations."""
    __tablename__ = "migration_record"

    version: Mapped[str] = mapped_column(
        String(ColLen.CODE), nullable=False, unique=True, comment="Alembic revision hash"
    )
    module: Mapped[str] = mapped_column(
        String(ColLen.NAME), nullable=False, comment="Module that owns this migration (e.g. _009_migration)"
    )
    description: Mapped[str] = mapped_column(
        String(ColLen.DESCRIPTION), nullable=False, default="", comment="Human-readable description of the migration"
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, comment="Timestamp when migration was applied"
    )
    applied_by: Mapped[str] = mapped_column(
        String(ColLen.SHORT_NAME), nullable=False, default="system", comment="User or process that applied the migration"
    )

    def __repr__(self) -> str:
        return f"<MigrationRecord {self.version} ({self.module})>"

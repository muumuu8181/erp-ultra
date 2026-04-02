"""
SQLAlchemy models for the Audit Log module.
"""
from typing import Any
from sqlalchemy import Integer, String, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from shared.types import Base


class AuditLog(Base):
    """
    AuditLog model to record critical actions across the system.
    """
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    changes: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

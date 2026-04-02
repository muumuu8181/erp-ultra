from typing import Any, Dict, Optional
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from shared.types import BaseModel

class LogEntry(BaseModel):
    """SQLAlchemy model for structured logging."""
    __tablename__ = "log_entries"

    level: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    trace_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

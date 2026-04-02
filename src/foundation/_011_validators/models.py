from typing import Any
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, JSON
from shared.types import BaseModel


class ValidationRule(BaseModel):
    """
    Model representing a dynamic validation rule.
    """
    __tablename__ = "validation_rules"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)

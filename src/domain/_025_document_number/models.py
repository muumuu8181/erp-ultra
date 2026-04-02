"""
ORM Models for Document Number Generator.
"""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel


class DocumentSequence(BaseModel):
    """
    ORM Model for tracking document number sequences.
    Inherits id, created_at, updated_at from BaseModel.
    """
    __tablename__ = "document_sequence"

    prefix: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    pattern: Mapped[str] = mapped_column(String(100), nullable=False)
    current_sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

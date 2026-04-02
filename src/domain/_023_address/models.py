"""
Database models for Address Book.
"""
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel


class Address(BaseModel):
    """Address Book entry."""
    __tablename__ = "addresses"
    __table_args__ = {'extend_existing': True}

    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    prefecture: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    street: Mapped[str] = mapped_column(String(200), nullable=False)
    building: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

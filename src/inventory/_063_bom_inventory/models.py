"""
SQLAlchemy models for BOM (Bill of Materials) and BOM items.
"""
from sqlalchemy import Integer, String, DateTime, ForeignKey, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from shared.types import Base


class BOM(Base):
    """
    Bill of Materials (BOM) model representing the assembly of a product.
    """
    __tablename__ = "bom"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["BOMItem"]] = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")


class BOMItem(Base):
    """
    BOM Item model representing a component part of a BOM.
    """
    __tablename__ = "bom_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bom_id: Mapped[int] = mapped_column(Integer, ForeignKey("bom.id"), nullable=False)
    component_id: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_required: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    uom: Mapped[str] = mapped_column(String(20), default="pcs", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    bom: Mapped["BOM"] = relationship("BOM", back_populates="items")

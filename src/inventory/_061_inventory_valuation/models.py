"""
SQLAlchemy models for inventory valuation.
"""
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import Integer, String, Date, DateTime, Boolean, Numeric, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import Base, BaseModel
from shared.schema import ColLen, Precision

# Allowed valuation methods based on Issue #51
VALUATION_METHODS = ("fifo", "lifo", "weighted_average", "standard_cost", "moving_average")


class ValuationMethod(BaseModel):
    """
    Method assigned to a product for inventory valuation.
    Only one method should be active per product at a time.
    """
    __tablename__ = "valuation_methods"

    product_code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    method: Mapped[str] = mapped_column(
        SQLEnum(*VALUATION_METHODS, name="valuation_method_enum"),
        nullable=False
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    standard_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4), nullable=True
    )


class ValuationSnapshot(Base):
    """
    Point-in-time snapshot of inventory value.
    """
    __tablename__ = "valuation_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    product_code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(*Precision.QUANTITY), nullable=False
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False
    )
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(*Precision.AMOUNT), nullable=False
    )
    method: Mapped[str] = mapped_column(
        SQLEnum(*VALUATION_METHODS, name="valuation_method_enum"),
        nullable=False
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class CostLayer(BaseModel):
    """
    Cost layers used for FIFO / LIFO tracking.
    """
    __tablename__ = "cost_layers"

    product_code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(*Precision.QUANTITY), nullable=False
    )
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(*Precision.QUANTITY), nullable=False
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False
    )
    layer_number: Mapped[int] = mapped_column(Integer, nullable=False)

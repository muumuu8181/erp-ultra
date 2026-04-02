from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, String, Numeric, Boolean, Date, DateTime, Enum as SQLEnum, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel


class ReorderPoint(BaseModel):
    __tablename__ = "reorder_points"

    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(50), nullable=False)
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    safety_stock: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    reorder_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    review_cycle: Mapped[str] = mapped_column(SQLEnum("daily", "weekly", "monthly", name="review_cycle_enum"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_reviewed: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("product_code", "warehouse_code", name="uq_reorder_points_product_warehouse"),
    )


class ReorderAlert(BaseModel):
    __tablename__ = "reorder_alerts"

    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(50), nullable=False)
    current_stock: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    deficit: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    status: Mapped[str] = mapped_column(SQLEnum("pending", "ordered", "resolved", name="alert_status_enum"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

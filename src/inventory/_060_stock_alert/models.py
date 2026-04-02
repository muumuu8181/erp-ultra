from sqlalchemy import Integer, String, Boolean, Numeric, DateTime, Text, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from shared.types import BaseModel


class AlertRule(BaseModel):
    __tablename__ = "alert_rules"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    warehouse_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    threshold_value: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    threshold_operator: Mapped[str] = mapped_column(String(50), nullable=False)
    comparison_field: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_users: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    alerts: Mapped[list["StockAlert"]] = relationship("StockAlert", back_populates="rule")


class StockAlert(BaseModel):
    __tablename__ = "stock_alerts"

    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("alert_rules.id"))
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(50), nullable=False)
    current_value: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    threshold_value: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    rule: Mapped["AlertRule"] = relationship("AlertRule", back_populates="alerts")

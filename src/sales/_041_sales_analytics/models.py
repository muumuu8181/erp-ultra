from datetime import date
from decimal import Decimal
from sqlalchemy import Integer, String, Date, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel

class SalesDailySummary(BaseModel):
    __tablename__ = "sales_daily_summaries"

    date: Mapped[date] = mapped_column(Date, nullable=False)
    customer_code: Mapped[str] = mapped_column(String(50), nullable=False)
    product_category: Mapped[str] = mapped_column(String(100), nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("date", "customer_code", "product_category", name="uq_sales_daily_summary"),
        {"extend_existing": True}
    )

class SalesTarget(BaseModel):
    __tablename__ = "sales_targets"

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    sales_person: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_group: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("year", "month", "sales_person", "customer_group", name="uq_sales_target"),
        {"extend_existing": True}
    )

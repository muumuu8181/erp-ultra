from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Date, DateTime, Boolean, Enum as SQLEnum, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
import enum
from shared.types import BaseModel


class DiscountType(str, enum.Enum):
    percentage = "percentage"
    fixed_amount = "fixed_amount"
    buy_x_get_y = "buy_x_get_y"


class AppliesTo(str, enum.Enum):
    order_total = "order_total"
    line_item = "line_item"
    shipping = "shipping"


class DiscountRule(BaseModel):
    __tablename__ = "discount_rule"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(SQLEnum(DiscountType), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    applies_to: Mapped[AppliesTo] = mapped_column(SQLEnum(AppliesTo), nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    customer_group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    min_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    is_stackable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)


class DiscountUsage(BaseModel):
    __tablename__ = "discount_usage"

    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("discount_rule.id"), nullable=False)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_code: Mapped[str] = mapped_column(String(50), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

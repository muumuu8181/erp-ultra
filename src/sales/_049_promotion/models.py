from datetime import date, datetime
from decimal import Decimal
import enum
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, Integer, JSON, Numeric, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.types import BaseModel


class PromotionType(str, enum.Enum):
    PERCENTAGE_OFF = "percentage_off"
    FIXED_OFF = "fixed_off"
    FREE_GIFT = "free_gift"
    BUNDLE = "bundle"
    BUY_X_GET_Y = "buy_x_get_y"


class Promotion(BaseModel):
    __tablename__ = "sales_promotion"
    __table_args__ = {"extend_existing": True}

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    promotion_type: Mapped[PromotionType] = mapped_column(Enum(PromotionType, name="promotion_type_enum"), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    product_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    customer_groups: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_redemptions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_redemptions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    redemptions: Mapped[List["PromotionRedemption"]] = relationship(
        "PromotionRedemption",
        back_populates="promotion",
        cascade="all, delete-orphan",
        primaryjoin="Promotion.id == PromotionRedemption.promotion_id"
    )


class PromotionRedemption(BaseModel):
    __tablename__ = "sales_promotion_redemption"
    __table_args__ = {"extend_existing": True}

    promotion_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_promotion.id"), nullable=False)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_code: Mapped[str] = mapped_column(String(50), nullable=False)
    redeemed_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    promotion: Mapped["Promotion"] = relationship(
        "src.sales._049_promotion.models.Promotion",
        back_populates="redemptions",
        primaryjoin="Promotion.id == PromotionRedemption.promotion_id"
    )

"""
Sales Forecast Models
"""
from datetime import date
from decimal import Decimal
from sqlalchemy import Integer, String, Date, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.types import BaseModel
from shared.schema import ColLen, Precision

class SalesForecast(BaseModel):
    """Sales Forecast model."""
    __tablename__ = "sales_forecast"

    code: Mapped[str] = mapped_column(String(ColLen.CODE), unique=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(ColLen.STATUS), default="draft")
    total_expected_revenue: Mapped[Decimal] = mapped_column(Numeric(*Precision.AMOUNT), default=Decimal('0.00'))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["SalesForecastItem"]] = relationship(
        "SalesForecastItem",
        back_populates="forecast",
        cascade="all, delete-orphan"
    )

class SalesForecastItem(BaseModel):
    """Sales Forecast Item model."""
    __tablename__ = "sales_forecast_item"

    forecast_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_forecast.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_quantity: Mapped[Decimal] = mapped_column(Numeric(*Precision.QUANTITY), default=Decimal('0.000'))
    expected_revenue: Mapped[Decimal] = mapped_column(Numeric(*Precision.AMOUNT), default=Decimal('0.00'))

    forecast: Mapped[SalesForecast] = relationship(
        "SalesForecast",
        back_populates="items"
    )

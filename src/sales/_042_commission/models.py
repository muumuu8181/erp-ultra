"""
Database models for Sales Commission module.
"""
from datetime import date
from decimal import Decimal
from sqlalchemy import Integer, String, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel
from shared.schema import ColLen, Precision, RowStatus

class Commission(BaseModel):
    """Sales Commission model."""
    __tablename__ = "sales_commission"
    __table_args__ = {'extend_existing': True}

    salesperson_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sales_order_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(*Precision.PERCENTAGE), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(*Precision.AMOUNT), nullable=False)
    currency: Mapped[str] = mapped_column(String(ColLen.CURRENCY), default="JPY")
    status: Mapped[str] = mapped_column(String(ColLen.STATUS), default=RowStatus.ACTIVE)
    calculation_date: Mapped[date] = mapped_column(Date, nullable=False)

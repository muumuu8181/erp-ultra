"""
SQLAlchemy models for Contract Management.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import Integer, String, Date, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel
from shared.schema import ColLen, Precision


class Contract(BaseModel):
    """
    Contract entity representing a sales contract with a customer.
    """
    __tablename__ = "sales_contract"

    contract_number: Mapped[str] = mapped_column(String(ColLen.CODE), unique=True, index=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String(ColLen.STATUS), default="draft", nullable=False)

    total_value: Mapped[Decimal] = mapped_column(Numeric(*Precision.AMOUNT), default=0, nullable=False)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(default=False)

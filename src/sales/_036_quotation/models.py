"""
Models for the _036_quotation module.
"""
from datetime import date
from typing import List

from sqlalchemy import Integer, String, Date, Text, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.types import BaseModel, DocumentStatus, TaxType
from shared.schema import ColLen, Precision


class Quotation(BaseModel):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_code: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quotation_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(SQLEnum(DocumentStatus), nullable=False, default=DocumentStatus.DRAFT)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    subtotal: Mapped[float] = mapped_column(Numeric(*Precision.AMOUNT), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(*Precision.AMOUNT), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(*Precision.AMOUNT), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sales_person: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    lines: Mapped[List["QuotationLine"]] = relationship("QuotationLine", back_populates="quotation", cascade="all, delete-orphan")


class QuotationLine(BaseModel):
    __tablename__ = "quotation_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(*Precision.QUANTITY), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="PCS")
    unit_price: Mapped[float] = mapped_column(Numeric(*Precision.AMOUNT), nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Numeric(*Precision.PERCENTAGE), nullable=False, default=0)
    tax_type: Mapped[TaxType] = mapped_column(SQLEnum(TaxType), nullable=False)
    line_amount: Mapped[float] = mapped_column(Numeric(*Precision.AMOUNT), nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="lines")

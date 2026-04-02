from enum import Enum
from datetime import date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Text, Numeric, Date, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.types import BaseModel, TaxType

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class Invoice(BaseModel):
    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    order_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_code: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        SQLAlchemyEnum(InvoiceStatus, native_enum=False, length=50),
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    payment_terms_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    billing_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine", back_populates="invoice", cascade="all, delete-orphan", primaryjoin="Invoice.id == InvoiceLine.invoice_id"
    )
    payments: Mapped[List["InvoicePayment"]] = relationship(
        "InvoicePayment", back_populates="invoice", cascade="all, delete-orphan", primaryjoin="Invoice.id == InvoicePayment.invoice_id"
    )

class InvoiceLine(BaseModel):
    __tablename__ = "invoice_lines"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    tax_type: Mapped[TaxType] = mapped_column(
        SQLAlchemyEnum(TaxType, native_enum=False, length=50), nullable=False
    )
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines", overlaps="lines")


class InvoicePayment(BaseModel):
    __tablename__ = "invoice_payments"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., bank_transfer / cash / check / credit_card
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments", overlaps="payments")

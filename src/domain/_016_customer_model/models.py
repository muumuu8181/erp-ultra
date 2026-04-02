from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.types import BaseModel


class CustomerContact(BaseModel):
    __tablename__ = "customer_contact"

    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customer.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")


class Customer(BaseModel):
    __tablename__ = "customer"

    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    name_kana: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    type: Mapped[str] = mapped_column(String(20)) # "corporate" or "individual"
    corporate_number: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)

    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    prefecture: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    street: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    building: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fax: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    payment_terms_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    tax_type: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    memo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # SoftDeleteMixin equivalent fields for sqlalchemy (as SoftDeleteMixin is a Pydantic schema in shared.types)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    contacts: Mapped[List[CustomerContact]] = relationship(
        "CustomerContact",
        back_populates="customer",
        cascade="all, delete-orphan"
    )

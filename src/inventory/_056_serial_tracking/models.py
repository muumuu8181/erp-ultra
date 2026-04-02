from sqlalchemy import Integer, String, Date, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import date, datetime
import enum

from shared.types import BaseModel


class SerialStatus(str, enum.Enum):
    in_stock = "in_stock"
    reserved = "reserved"
    shipped = "shipped"
    in_repair = "in_repair"
    scrapped = "scrapped"


class SerialEventType(str, enum.Enum):
    received = "received"
    stored = "stored"
    reserved = "reserved"
    shipped = "shipped"
    returned = "returned"
    transferred = "transferred"
    repaired = "repaired"
    scrapped = "scrapped"


class SerialNumber(BaseModel):
    __tablename__ = "serial_numbers"
    __table_args__ = {'extend_existing': True}

    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(50), nullable=False)
    bin_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[SerialStatus] = mapped_column(Enum(SerialStatus), nullable=False)
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sale_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    warranty_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    warranty_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SerialHistory(BaseModel):
    __tablename__ = "serial_history"
    __table_args__ = {'extend_existing': True}

    serial_id: Mapped[int] = mapped_column(Integer, ForeignKey("serial_numbers.id"), nullable=False)
    event_type: Mapped[SerialEventType] = mapped_column(Enum(SerialEventType), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[str] = mapped_column(String(50), nullable=False)
    location_from: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

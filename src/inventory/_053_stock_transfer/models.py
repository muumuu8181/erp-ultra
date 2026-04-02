"""
Stock Transfer models.
"""
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.schema import TABLE_PREFIX, ColLen, Precision
from shared.types import Base


class StockTransfer(Base):
    """Model representing a stock transfer between warehouses."""
    __tablename__ = f"{TABLE_PREFIX}stock_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_number: Mapped[str] = mapped_column(String(ColLen.CODE), unique=True, nullable=False)
    from_warehouse: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    to_warehouse: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("draft", "in_transit", "received", "cancelled", name="stock_transfer_status"),
        nullable=False,
        default="draft"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now()
    )

    lines: Mapped[List["StockTransferLine"]] = relationship(
        "StockTransferLine",
        back_populates="transfer",
        cascade="all, delete-orphan",
    )


class StockTransferLine(Base):
    """Model representing an item line in a stock transfer."""
    __tablename__ = f"{TABLE_PREFIX}stock_transfer_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{TABLE_PREFIX}stock_transfers.id"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    product_name: Mapped[str] = mapped_column(String(ColLen.NAME), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(*Precision.QUANTITY), nullable=False)
    lot_number: Mapped[Optional[str]] = mapped_column(String(ColLen.CODE), nullable=True)
    received_quantity: Mapped[Optional[float]] = mapped_column(Numeric(*Precision.QUANTITY), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now()
    )

    transfer: Mapped[StockTransfer] = relationship("StockTransfer", back_populates="lines")

"""
Sales Order Models
"""
from decimal import Decimal
from typing import List

from sqlalchemy import Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.types import BaseModel, DocumentStatus
from shared.schema import ColLen, Precision


class SalesOrder(BaseModel):
    __tablename__ = "sales_orders"

    code: Mapped[str] = mapped_column(String(ColLen.CODE), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(ColLen.STATUS), default=DocumentStatus.DRAFT.value, nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(*Precision.AMOUNT), default=Decimal("0.00"), nullable=False
    )

    items: Mapped[List["SalesOrderItem"]] = relationship(
        "SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan"
    )


class SalesOrderItem(BaseModel):
    __tablename__ = "sales_order_items"

    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(*Precision.QUANTITY), nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(*Precision.AMOUNT), nullable=False
    )

    sales_order: Mapped[SalesOrder] = relationship(
        "SalesOrder", back_populates="items"
    )

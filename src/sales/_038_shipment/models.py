from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.types import BaseModel

class Shipment(BaseModel):
    """SQLAlchemy model for a shipment header."""
    __tablename__ = "sales_shipments"

    sales_order_id: Mapped[int] = mapped_column(Integer, nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expected_delivery_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["ShipmentItem"]] = relationship(
        "ShipmentItem", back_populates="shipment", cascade="all, delete-orphan"
    )

class ShipmentItem(BaseModel):
    """SQLAlchemy model for a shipment line item."""
    __tablename__ = "sales_shipment_items"

    shipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_shipments.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)

    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="items")

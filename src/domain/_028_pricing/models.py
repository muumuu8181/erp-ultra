from typing import Optional
from datetime import date
from decimal import Decimal

from sqlalchemy import String, Date, Boolean, Numeric, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel
from shared.schema import ColLen, Precision

class PriceList(BaseModel):
    """Price list with date-bounded validity."""
    __tablename__ = "price_list"

    name: Mapped[str] = mapped_column(String(ColLen.NAME), nullable=False)
    code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False, unique=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency_code: Mapped[str] = mapped_column(String(ColLen.CURRENCY), nullable=False, default='JPY')
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PriceListItem(BaseModel):
    """Price entry within a price list."""
    __tablename__ = "price_list_item"
    __table_args__ = (
        Index('ix_price_item_list_product', 'price_list_id', 'product_code'),
        Index('ix_price_item_list_product_qty', 'price_list_id', 'product_code', 'min_quantity'),
    )

    price_list_id: Mapped[int] = mapped_column(Integer, ForeignKey('price_list.id'), nullable=False)
    product_code: Mapped[str] = mapped_column(String(ColLen.CODE), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(*Precision.AMOUNT), nullable=False)
    discount_percentage: Mapped[Decimal] = mapped_column(Numeric(*Precision.PERCENTAGE), nullable=False, default=0)
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(*Precision.QUANTITY), nullable=False, default=1)

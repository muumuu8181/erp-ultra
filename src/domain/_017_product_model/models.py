from sqlalchemy import Integer, String, DateTime, Numeric, Boolean, Text, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.types import Base, BaseModel
from datetime import datetime
from decimal import Decimal

class ProductCategory(BaseModel):
    __tablename__ = "product_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("product_category.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    parent: Mapped["ProductCategory | None"] = relationship("ProductCategory", remote_side=[id])

    # Audit fields
    created_by: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    updated_by: Mapped[str] = mapped_column(String(50), nullable=False, default="system")

class Product(BaseModel):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_kana: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sub_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    standard_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_type: Mapped[str] = mapped_column(Enum("standard_10", "reduced_8", "exempt", "non_taxable", name="tax_type_enum"), nullable=False)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    weight_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    barcode: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    reorder_point: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)
    safety_stock: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)
    lot_size: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit fields
    created_by: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    updated_by: Mapped[str] = mapped_column(String(50), nullable=False, default="system")

    # SoftDelete fields
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

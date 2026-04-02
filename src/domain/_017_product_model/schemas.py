from decimal import Decimal
from typing import Literal
from datetime import datetime
from pydantic import ConfigDict
from shared.types import BaseSchema

class ProductCreate(BaseSchema):
    """Schema for creating a new product."""
    code: str  # PRD-XXXXX format
    name: str
    name_kana: str | None = None
    description: str | None = None
    category: str | None = None
    sub_category: str | None = None
    unit: str  # Must be one of: pcs, kg, m, l, box, set, pair, roll, sheet
    standard_price: Decimal
    cost_price: Decimal
    tax_type: Literal["standard_10", "reduced_8", "exempt", "non_taxable"]
    weight: Decimal | None = None
    weight_unit: str | None = None
    is_active: bool = True
    barcode: str | None = None
    supplier_id: int | None = None
    lead_time_days: int = 0
    reorder_point: Decimal | None = None
    safety_stock: Decimal | None = None
    lot_size: Decimal | None = None
    memo: str | None = None


class ProductUpdate(BaseSchema):
    """Schema for updating an existing product. All fields optional."""
    name: str | None = None
    name_kana: str | None = None
    description: str | None = None
    category: str | None = None
    sub_category: str | None = None
    unit: str | None = None
    standard_price: Decimal | None = None
    cost_price: Decimal | None = None
    tax_type: Literal["standard_10", "reduced_8", "exempt", "non_taxable"] | None = None
    weight: Decimal | None = None
    weight_unit: str | None = None
    is_active: bool | None = None
    barcode: str | None = None
    supplier_id: int | None = None
    lead_time_days: int | None = None
    reorder_point: Decimal | None = None
    safety_stock: Decimal | None = None
    lot_size: Decimal | None = None
    memo: str | None = None


class ProductResponse(BaseSchema):
    """Schema for product API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_kana: str | None
    description: str | None
    category: str | None
    sub_category: str | None
    unit: str
    standard_price: Decimal
    cost_price: Decimal
    tax_type: str
    weight: Decimal | None
    weight_unit: str | None
    is_active: bool
    barcode: str | None
    supplier_id: int | None
    lead_time_days: int
    reorder_point: Decimal | None
    safety_stock: Decimal | None
    lot_size: Decimal | None
    memo: str | None
    created_at: datetime
    updated_at: datetime


class ProductCategoryCreate(BaseSchema):
    """Schema for creating a product category."""
    name: str
    parent_id: int | None = None
    sort_order: int = 0
    is_active: bool = True


class ProductCategoryResponse(BaseSchema):
    """Schema for product category API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductSearchFilter(BaseSchema):
    """Schema for product search/filter."""
    query: str | None = None
    category: str | None = None
    sub_category: str | None = None
    is_active: bool | None = None
    tax_type: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    supplier_id: int | None = None

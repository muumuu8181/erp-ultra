import re
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.errors import ValidationError, NotFoundError
from src.domain._017_product_model.schemas import ProductCreate, ProductUpdate
from src.domain._017_product_model.models import ProductCategory

def validate_product_code(code: str) -> None:
    """Validate product code format: must match PRD-XXXXX where X is alphanumeric.
    Raises ValidationError if format is invalid."""
    if not re.match(r"^PRD-[a-zA-Z0-9]{5}$", code):
        raise ValidationError("Invalid product code format. Must match PRD-XXXXX")

def validate_positive_price(price: Decimal, field_name: str) -> None:
    """Validate that a price value is >= 0.
    Raises ValidationError with field name if price is negative."""
    if price < Decimal("0"):
        raise ValidationError(f"{field_name} cannot be negative")

def validate_unit(unit: str) -> None:
    """Validate unit of measure. Allowed values: pcs, kg, m, l, box, set, pair, roll, sheet.
    Raises ValidationError if unit is not in the allowed list."""
    allowed_units = {"pcs", "kg", "m", "l", "box", "set", "pair", "roll", "sheet"}
    if unit not in allowed_units:
        raise ValidationError(f"Invalid unit: {unit}. Must be one of {allowed_units}")

async def validate_category_exists(db: AsyncSession, category_name: str) -> None:
    """Validate that a category name exists in ProductCategory table (if provided).
    Raises NotFoundError if category not found.
    Note: This is optional validation - only enforced when linking to categories."""
    if category_name:
        result = await db.execute(select(ProductCategory).where(ProductCategory.name == category_name))
        if not result.scalars().first():
            raise NotFoundError(f"Category '{category_name}' not found")

def validate_product_create(data: ProductCreate) -> None:
    """Run all validations for product creation.
    Validates: code format, positive prices, valid unit."""
    validate_product_code(data.code)
    validate_positive_price(data.standard_price, "standard_price")
    validate_positive_price(data.cost_price, "cost_price")
    validate_unit(data.unit)

def validate_product_update(data: ProductUpdate) -> None:
    """Run all validations for product update (only for non-None fields)."""
    if data.unit is not None:
        validate_unit(data.unit)
    if data.standard_price is not None:
        validate_positive_price(data.standard_price, "standard_price")
    if data.cost_price is not None:
        validate_positive_price(data.cost_price, "cost_price")

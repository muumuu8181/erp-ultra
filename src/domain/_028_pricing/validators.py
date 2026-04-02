import re
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError

def validate_date_range(valid_from: date, valid_to: Optional[date]) -> None:
    """Validate that valid_from <= valid_to."""
    if valid_to is not None and valid_from > valid_to:
        raise ValidationError("valid_from must be less than or equal to valid_to")

def validate_positive_price(value: Decimal) -> Decimal:
    """Validate that unit price is positive."""
    if value <= 0:
        raise ValidationError("Unit price must be positive")
    return value

def validate_discount_percentage(value: Decimal) -> Decimal:
    """Validate that discount percentage is between 0 and 100."""
    if value < 0 or value > 100:
        raise ValidationError("Discount percentage must be between 0 and 100")
    return value

async def validate_product_code_exists(db: AsyncSession, product_code: str) -> None:
    """Validate that a product code exists."""
    if not product_code or not product_code.strip():
        raise ValidationError("Product code cannot be empty")

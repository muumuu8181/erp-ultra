"""
Validation logic for BOM inventory module.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import ValidationError, BusinessRuleError
from src.inventory._063_bom_inventory.models import BOM, BOMItem


def validate_positive_quantity(quantity: int) -> None:
    """Validates that a quantity is greater than zero."""
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero", field="quantity")


async def validate_circular_dependency(db: AsyncSession, product_id: str, new_component_id: str) -> None:
    """
    Validates that adding `new_component_id` to a BOM for `product_id`
    does not create a circular dependency.
    """
    if product_id == new_component_id:
        raise BusinessRuleError("A product cannot be a component of itself.")

    # A simple cycle check: does the new component have a BOM where the product is a component?
    # This checks one level down for cycles.
    stmt = (
        select(BOMItem)
        .join(BOM)
        .where(BOM.product_id == new_component_id)
        .where(BOMItem.component_id == product_id)
    )
    result = await db.execute(stmt)
    if result.scalars().first() is not None:
        raise BusinessRuleError("Circular dependency detected.")

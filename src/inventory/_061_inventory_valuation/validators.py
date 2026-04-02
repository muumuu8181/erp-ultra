"""
Validators and business rules for inventory valuation.
"""
from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, ValidationError, CalculationError
from src.inventory._061_inventory_valuation.models import ValuationMethod, CostLayer


async def validate_one_method_per_product(db: AsyncSession, product_code: str) -> None:
    """
    Ensure only one active valuation method exists for a product at a time.
    Raises DuplicateError if an active method already exists (to be caught and deactivated in service).
    """
    result = await db.execute(
        select(ValuationMethod).where(
            ValuationMethod.product_code == product_code,
            ValuationMethod.is_active == True
        )
    )
    if result.scalars().first():
        raise DuplicateError("ValuationMethod", product_code)


def validate_positive_unit_cost(unit_cost: Decimal) -> None:
    """
    Unit cost must be > 0.
    """
    if unit_cost <= 0:
        raise ValidationError("Unit cost must be positive.", field="unit_cost")


def validate_method_enum(method: str) -> None:
    """
    Method must be one of the allowed valuation methods.
    """
    allowed_methods = {"fifo", "lifo", "weighted_average", "standard_cost", "moving_average"}
    if method not in allowed_methods:
        raise ValidationError(f"Invalid valuation method: {method}", field="method")


def consume_fifo(layers: list[CostLayer], quantity_to_consume: Decimal) -> list[CostLayer]:
    """
    Consume layers FIFO (oldest first).
    Expects layers sorted by received_date ASC, layer_number ASC.
    """
    consumed_layers = []
    remaining_qty = quantity_to_consume

    for layer in layers:
        if remaining_qty <= 0:
            break

        if layer.remaining_quantity <= 0:
            continue

        consume_amount = min(layer.remaining_quantity, remaining_qty)
        layer.remaining_quantity -= consume_amount
        remaining_qty -= consume_amount
        consumed_layers.append(layer)

    if remaining_qty > 0:
        raise CalculationError("Not enough inventory to consume.")

    return consumed_layers


def consume_average(layers: list[CostLayer], quantity_to_consume: Decimal) -> list[CostLayer]:
    """
    Consume layers using average costing logic.
    For true moving average, we do not consume oldest layers first.
    Instead, we reduce the inventory proportionally across all layers,
    or simply reduce oldest layers sequentially but at the average cost.
    However, since layers have individual unit costs, reducing oldest layers
    would change the remaining average cost.

    A simpler and robust method to maintain the current average cost is to
    reduce quantity proportionally across all available layers.
    """
    consumed_layers = []
    remaining_qty = quantity_to_consume
    total_qty = sum(layer.remaining_quantity for layer in layers)

    if remaining_qty > total_qty:
        raise CalculationError("Not enough inventory to consume.")

    for layer in layers:
        if remaining_qty <= 0:
            break

        if layer.remaining_quantity <= 0:
            continue

        # Proportion of this layer to the total inventory
        proportion = layer.remaining_quantity / total_qty
        consume_amount = min(layer.remaining_quantity, quantity_to_consume * proportion)

        # In case of tiny rounding issues, we adjust at the last layer, but simple logic:
        # We can just consume FIFO but for moving average it means the value is drawn down.
        # Actually, reducing the remaining quantity of all layers proportionally preserves the exact average unit cost!

        layer.remaining_quantity -= consume_amount
        remaining_qty -= consume_amount
        consumed_layers.append(layer)

    # If due to rounding we still have some remaining quantity to consume, consume it from the first available layer
    for layer in layers:
        if remaining_qty <= 0:
            break
        if layer.remaining_quantity > 0:
            consume_amount = min(layer.remaining_quantity, remaining_qty)
            layer.remaining_quantity -= consume_amount
            remaining_qty -= consume_amount
            if layer not in consumed_layers:
                consumed_layers.append(layer)

    if remaining_qty > Decimal('0.0001'):
        raise CalculationError("Not enough inventory to consume.")

    return consumed_layers


def consume_lifo(layers: list[CostLayer], quantity_to_consume: Decimal) -> list[CostLayer]:
    """
    Consume layers LIFO (newest first).
    Expects layers sorted by received_date DESC, layer_number DESC.
    """
    # Logic is identical to FIFO, but the list input should be sorted differently by the service.
    consumed_layers = []
    remaining_qty = quantity_to_consume

    for layer in layers:
        if remaining_qty <= 0:
            break

        if layer.remaining_quantity <= 0:
            continue

        consume_amount = min(layer.remaining_quantity, remaining_qty)
        layer.remaining_quantity -= consume_amount
        remaining_qty -= consume_amount
        consumed_layers.append(layer)

    if remaining_qty > 0:
        raise CalculationError("Not enough inventory to consume.")

    return consumed_layers


def calculate_weighted_average(layers: list[CostLayer]) -> Decimal:
    """
    Calculate running average = sum(layer.remaining_quantity * layer.unit_cost) / sum(layer.remaining_quantity).
    """
    total_qty = sum(layer.remaining_quantity for layer in layers)
    if total_qty <= 0:
        return Decimal('0')

    total_value = sum(layer.remaining_quantity * layer.unit_cost for layer in layers)
    return total_value / total_qty

import math
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import ValidationError, DuplicateError, CalculationError
from .models import ReorderPoint


async def validate_reorder_point_logic(reorder_point: Decimal, safety_stock: Decimal) -> None:
    """Validate that the reorder point is at or above safety stock."""
    if reorder_point < safety_stock:
        raise ValidationError(
            "Reorder point must be at or above safety stock level",
            field="reorder_point"
        )


async def validate_reorder_quantity(reorder_quantity: Decimal) -> None:
    """Validate that the reorder quantity is strictly positive."""
    if reorder_quantity <= 0:
        raise ValidationError(
            "Reorder quantity must be positive",
            field="reorder_quantity"
        )


async def validate_lead_time_days(lead_time_days: int) -> None:
    """Validate that lead time is at least 1 day."""
    if lead_time_days < 1:
        raise ValidationError(
            "Lead time must be at least 1 day",
            field="lead_time_days"
        )


async def validate_unique_product_warehouse(
    db: AsyncSession, product_code: str, warehouse_code: str, exclude_id: int | None = None
) -> None:
    """Ensure no duplicate reorder point for the same product+warehouse."""
    stmt = select(ReorderPoint).where(
        ReorderPoint.product_code == product_code,
        ReorderPoint.warehouse_code == warehouse_code
    )
    if exclude_id is not None:
        stmt = stmt.where(ReorderPoint.id != exclude_id)

    result = await db.execute(stmt)
    if result.scalars().first() is not None:
        raise DuplicateError(
            resource="ReorderPoint",
            key=f"{product_code}-{warehouse_code}"
        )


def calculate_safety_stock_formula(
    demand_std_dev: Decimal, lead_time_days: int, service_level_z: Decimal
) -> Decimal:
    """
    Calculate safety stock using the formula: Z * sigma * sqrt(LT).
    """
    if demand_std_dev < 0 or lead_time_days < 0 or service_level_z < 0:
        raise CalculationError("Parameters for safety stock calculation must be non-negative.")

    # math.sqrt takes float, so convert Decimal to float and back
    lt_sqrt = Decimal(str(math.sqrt(float(lead_time_days))))

    safety_stock = service_level_z * demand_std_dev * lt_sqrt
    # Round to 3 decimal places to match DB schema
    return safety_stock.quantize(Decimal("0.001"))


def calculate_eoq_formula(
    annual_demand: Decimal, ordering_cost: Decimal, holding_cost_pct: Decimal, unit_cost: Decimal | None = None
) -> Decimal:
    """
    Suggest reorder quantity using EOQ formula: sqrt(2 * D * S / H)
    If unit_cost is provided, H = holding_cost_pct * unit_cost
    Else we assume holding_cost_pct is the actual holding cost (H)
    """
    if annual_demand <= 0 or ordering_cost <= 0 or holding_cost_pct <= 0:
        raise CalculationError("EOQ parameters must be strictly positive.")

    H = holding_cost_pct
    if unit_cost is not None:
        if unit_cost <= 0:
            raise CalculationError("Unit cost must be strictly positive.")
        H = holding_cost_pct * unit_cost

    try:
        val = 2 * annual_demand * ordering_cost / H
        eoq = Decimal(str(math.sqrt(float(val))))
        # Round to 3 decimal places to match DB schema
        return eoq.quantize(Decimal("0.001"))
    except Exception as e:
        raise CalculationError(f"Error calculating EOQ: {str(e)}")

import math
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared.errors import NotFoundError, CalculationError
from shared.types import PaginatedResponse
from .models import ReorderPoint, ReorderAlert
from .schemas import ReorderPointCreate, ReorderPointUpdate, ReorderSuggestion, AlertStatusEnum, ReorderPointResponse, ReorderAlertResponse
from .validators import (
    validate_reorder_point_logic,
    validate_reorder_quantity,
    validate_lead_time_days,
    validate_unique_product_warehouse,
    calculate_safety_stock_formula,
    calculate_eoq_formula
)


async def create_reorder_point(db: AsyncSession, data: ReorderPointCreate) -> ReorderPoint:
    """Create a new reorder point configuration."""
    await validate_reorder_point_logic(data.reorder_point, data.safety_stock)
    await validate_reorder_quantity(data.reorder_quantity)
    await validate_lead_time_days(data.lead_time_days)
    await validate_unique_product_warehouse(db, data.product_code, data.warehouse_code)

    rp = ReorderPoint(
        product_code=data.product_code,
        warehouse_code=data.warehouse_code,
        reorder_point=data.reorder_point,
        safety_stock=data.safety_stock,
        reorder_quantity=data.reorder_quantity,
        lead_time_days=data.lead_time_days,
        review_cycle=data.review_cycle.value,
        is_active=data.is_active,
        last_reviewed=data.last_reviewed
    )
    db.add(rp)
    await db.flush()
    return rp


async def update_reorder_point(db: AsyncSession, reorder_id: int, data: ReorderPointUpdate) -> ReorderPoint:
    """Update an existing reorder point configuration."""
    rp = await db.get(ReorderPoint, reorder_id)
    if not rp:
        raise NotFoundError("ReorderPoint", str(reorder_id))

    new_reorder_point = data.reorder_point if data.reorder_point is not None else rp.reorder_point
    new_safety_stock = data.safety_stock if data.safety_stock is not None else rp.safety_stock

    await validate_reorder_point_logic(new_reorder_point, new_safety_stock)

    if data.reorder_quantity is not None:
        await validate_reorder_quantity(data.reorder_quantity)
    if data.lead_time_days is not None:
        await validate_lead_time_days(data.lead_time_days)

    if data.reorder_point is not None:
        rp.reorder_point = data.reorder_point
    if data.safety_stock is not None:
        rp.safety_stock = data.safety_stock
    if data.reorder_quantity is not None:
        rp.reorder_quantity = data.reorder_quantity
    if data.lead_time_days is not None:
        rp.lead_time_days = data.lead_time_days
    if data.review_cycle is not None:
        rp.review_cycle = data.review_cycle.value
    if data.is_active is not None:
        rp.is_active = data.is_active
    if data.last_reviewed is not None:
        rp.last_reviewed = data.last_reviewed

    await db.flush()
    return rp


async def get_reorder_point(db: AsyncSession, reorder_id: int) -> ReorderPoint:
    """Get a reorder point by ID."""
    rp = await db.get(ReorderPoint, reorder_id)
    if not rp:
        raise NotFoundError("ReorderPoint", str(reorder_id))
    return rp


async def delete_reorder_point(db: AsyncSession, reorder_id: int) -> None:
    """Delete a reorder point by ID."""
    rp = await db.get(ReorderPoint, reorder_id)
    if not rp:
        raise NotFoundError("ReorderPoint", str(reorder_id))

    await db.delete(rp)
    await db.flush()


async def list_reorder_points(
    db: AsyncSession, warehouse_code: str | None = None, is_active: bool | None = None, page: int = 1, page_size: int = 50
) -> PaginatedResponse[ReorderPointResponse]:
    """List reorder points with optional filters."""
    stmt = select(ReorderPoint)
    if warehouse_code is not None:
        stmt = stmt.where(ReorderPoint.warehouse_code == warehouse_code)
    if is_active is not None:
        stmt = stmt.where(ReorderPoint.is_active == is_active)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt) or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    response_items = [ReorderPointResponse.model_validate(item) for item in items]

    return PaginatedResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def check_reorder_points(db: AsyncSession, warehouse_code: str | None = None) -> list[ReorderAlert]:
    """Check all active reorder points against current stock levels and generate alerts."""
    # In a real system, we'd query the inventory module or inventory_balances table
    # Since we can't assume how current stock is stored without seeing it, we'll implement
    # a mock/stub that would be replaced by actual inventory querying.
    # The requirement specifically mentions "generate alerts for products below their reorder point."
    # We will assume `generate_alerts` is an alias or does exactly what this does,
    # but the requirement gives us two signatures. Let's make one call the other.
    return await generate_alerts(db, warehouse_code)


async def generate_alerts(db: AsyncSession, warehouse_code: str | None = None) -> list[ReorderAlert]:
    """Generate reorder alerts for products below their reorder point."""
    stmt = select(ReorderPoint).where(ReorderPoint.is_active == True)
    if warehouse_code is not None:
        stmt = stmt.where(ReorderPoint.warehouse_code == warehouse_code)

    result = await db.execute(stmt)
    reorder_points = result.scalars().all()

    alerts = []
    for rp in reorder_points:
        # Mocking current stock for the sake of module isolation/testability based on requirements.
        # Ideally, we'd query: select current_qty from stock_balances where product_code=rp.product_code...
        # Since it's not defined, let's just assume we check some interface.
        # For tests, we will provide a way to inject current_stock or just mock it.
        # Actually, let's do a stub `get_current_stock` that returns 0 for now so tests can patch it
        # or we just assume a deficit of reorder_point for the alert.
        current_stock = await _get_current_stock_stub(db, rp.product_code, rp.warehouse_code)

        if current_stock < rp.reorder_point:
            deficit = rp.reorder_point - current_stock

            # Check if an unresolved alert already exists
            existing_alert_stmt = select(ReorderAlert).where(
                ReorderAlert.product_code == rp.product_code,
                ReorderAlert.warehouse_code == rp.warehouse_code,
                ReorderAlert.status.in_([AlertStatusEnum.PENDING.value, AlertStatusEnum.ORDERED.value])
            )
            existing = await db.scalar(existing_alert_stmt)

            if not existing:
                alert = ReorderAlert(
                    product_code=rp.product_code,
                    warehouse_code=rp.warehouse_code,
                    current_stock=current_stock,
                    reorder_point=rp.reorder_point,
                    deficit=deficit,
                    status=AlertStatusEnum.PENDING.value
                )
                db.add(alert)
                alerts.append(alert)

    if alerts:
        await db.flush()
    return alerts


async def _get_current_stock_stub(db: AsyncSession, product_code: str, warehouse_code: str) -> Decimal:
    """Stub to get current stock. In real system, calls inventory api."""
    # This is a stub for the tests to patch or mock.
    return Decimal("0.000")


async def get_alerts(
    db: AsyncSession, status: str | None = None, page: int = 1, page_size: int = 50
) -> PaginatedResponse[ReorderAlertResponse]:
    """List reorder alerts with optional status filter."""
    stmt = select(ReorderAlert)
    if status is not None:
        stmt = stmt.where(ReorderAlert.status == status)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt) or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    response_items = [ReorderAlertResponse.model_validate(item) for item in items]

    return PaginatedResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def resolve_alert(db: AsyncSession, alert_id: int) -> ReorderAlert:
    """Mark a reorder alert as resolved."""
    from datetime import datetime

    alert = await db.get(ReorderAlert, alert_id)
    if not alert:
        raise NotFoundError("ReorderAlert", str(alert_id))

    alert.status = AlertStatusEnum.RESOLVED.value
    alert.resolved_at = datetime.utcnow()
    await db.flush()
    return alert


async def calculate_safety_stock(
    db: AsyncSession, reorder_id: int, demand_std_dev: Decimal, lead_time_days: int, service_level_z: Decimal = Decimal("1.65")
) -> Decimal:
    """Calculate safety stock using the formula: Z * sigma * sqrt(LT)."""
    # Fetch reorder point to make sure it exists, though formula could be detached
    rp = await db.get(ReorderPoint, reorder_id)
    if not rp:
        raise NotFoundError("ReorderPoint", str(reorder_id))

    return calculate_safety_stock_formula(demand_std_dev, lead_time_days, service_level_z)


async def suggest_reorder_quantity(
    db: AsyncSession, reorder_id: int, annual_demand: Decimal | None = None, ordering_cost: Decimal | None = None, holding_cost_pct: Decimal | None = None
) -> ReorderSuggestion:
    """Suggest reorder quantity using EOQ formula or fixed quantity fallback."""
    rp = await db.get(ReorderPoint, reorder_id)
    if not rp:
        raise NotFoundError("ReorderPoint", str(reorder_id))

    if annual_demand is not None and ordering_cost is not None and holding_cost_pct is not None:
        try:
            suggested_qty = calculate_eoq_formula(annual_demand, ordering_cost, holding_cost_pct)
            rationale = "Calculated using Economic Order Quantity (EOQ) formula."
        except CalculationError as e:
            suggested_qty = rp.reorder_quantity
            rationale = f"EOQ calculation failed ({str(e)}). Falling back to fixed reorder quantity."
    else:
        suggested_qty = rp.reorder_quantity
        rationale = "Insufficient data for EOQ calculation. Using configured fixed reorder quantity."

    return ReorderSuggestion(suggested_quantity=suggested_qty, rationale=rationale)

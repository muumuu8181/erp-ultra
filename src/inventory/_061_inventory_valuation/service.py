"""
Business logic service for inventory valuation.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select, update, func, desc, null
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError, ValidationError, CalculationError
from src.inventory._061_inventory_valuation.models import ValuationMethod, CostLayer, ValuationSnapshot
from src.inventory._061_inventory_valuation.schemas import (
    ValuationMethodCreate,
    ValuationSnapshotResponse,
    ValuationReport,
    ValuationReportItem,
    ValuationSummary,
    ValuationSummaryItem
)
from src.inventory._061_inventory_valuation.validators import (
    validate_positive_unit_cost,
    validate_method_enum,
    consume_fifo,
    consume_lifo,
    calculate_weighted_average
)


async def set_valuation_method(db: AsyncSession, data: ValuationMethodCreate) -> ValuationMethod:
    """Set the valuation method for a product. Deactivates previous method."""
    validate_method_enum(data.method)

    # Deactivate previous method
    await db.execute(
        update(ValuationMethod)
        .where(ValuationMethod.product_code == data.product_code, ValuationMethod.is_active == True)
        .values(is_active=False)
    )

    new_method = ValuationMethod(
        product_code=data.product_code,
        method=data.method,
        effective_from=data.effective_from,
        is_active=True,
        standard_cost=data.standard_cost
    )
    db.add(new_method)
    await db.flush()
    return new_method


async def get_valuation_method(db: AsyncSession, product_code: str) -> ValuationMethod:
    """Get the active valuation method for a product."""
    result = await db.execute(
        select(ValuationMethod).where(
            ValuationMethod.product_code == product_code,
            ValuationMethod.is_active == True
        )
    )
    method = result.scalars().first()
    if not method:
        raise NotFoundError("ValuationMethod", product_code)
    return method


async def add_cost_layer(
    db: AsyncSession, product_code: str, warehouse_code: str, received_date: date, quantity: Decimal, unit_cost: Decimal
) -> CostLayer:
    """Add a new cost layer when inventory is received."""
    validate_positive_unit_cost(unit_cost)
    if quantity <= 0:
        raise ValidationError("Quantity must be positive.", field="quantity")

    # Get max layer number
    result = await db.execute(
        select(func.max(CostLayer.layer_number))
        .where(CostLayer.product_code == product_code, CostLayer.warehouse_code == warehouse_code)
    )
    max_layer = result.scalar()
    layer_number = 1 if max_layer is None else max_layer + 1

    layer = CostLayer(
        product_code=product_code,
        warehouse_code=warehouse_code,
        received_date=received_date,
        quantity=quantity,
        remaining_quantity=quantity,
        unit_cost=unit_cost,
        layer_number=layer_number
    )
    db.add(layer)
    await db.flush()
    return layer


async def consume_cost_layer(
    db: AsyncSession, product_code: str, warehouse_code: str, quantity: Decimal, method: str
) -> list[CostLayer]:
    """Consume cost layers based on valuation method. FIFO: oldest first, LIFO: newest first."""
    if quantity <= 0:
        raise ValidationError("Quantity to consume must be positive.", field="quantity")

    validate_method_enum(method)

    if method in ("fifo", "standard_cost"):
        # FIFO or standard_cost sorting: oldest first
        result = await db.execute(
            select(CostLayer).where(
                CostLayer.product_code == product_code,
                CostLayer.warehouse_code == warehouse_code,
                CostLayer.remaining_quantity > 0
            ).order_by(CostLayer.received_date.asc(), CostLayer.layer_number.asc())
        )
        layers = list(result.scalars().all())
        consumed = consume_fifo(layers, quantity)
    elif method == "lifo":
        # LIFO sorting: newest first
        result = await db.execute(
            select(CostLayer).where(
                CostLayer.product_code == product_code,
                CostLayer.warehouse_code == warehouse_code,
                CostLayer.remaining_quantity > 0
            ).order_by(CostLayer.received_date.desc(), CostLayer.layer_number.desc())
        )
        layers = list(result.scalars().all())
        consumed = consume_lifo(layers, quantity)
    elif method in ("weighted_average", "moving_average"):
        from src.inventory._061_inventory_valuation.validators import consume_average
        result = await db.execute(
            select(CostLayer).where(
                CostLayer.product_code == product_code,
                CostLayer.warehouse_code == warehouse_code,
                CostLayer.remaining_quantity > 0
            ).order_by(CostLayer.received_date.asc(), CostLayer.layer_number.asc())
        )
        layers = list(result.scalars().all())
        consumed = consume_average(layers, quantity)
    else:
        raise CalculationError(f"Consumption for method {method} not implemented.")

    return consumed


async def calculate_valuation(
    db: AsyncSession, product_code: str, warehouse_code: str | None = None
) -> list[ValuationSnapshotResponse]:
    """Calculate current valuation for a product using its assigned method."""
    method_record = await get_valuation_method(db, product_code)
    method = method_record.method

    query = select(CostLayer).where(
        CostLayer.product_code == product_code,
        CostLayer.remaining_quantity > 0
    )
    if warehouse_code:
        query = query.where(CostLayer.warehouse_code == warehouse_code)

    result = await db.execute(query)
    layers = list(result.scalars().all())

    # Group by warehouse
    warehouse_layers: dict[str, list[CostLayer]] = {}
    for layer in layers:
        warehouse_layers.setdefault(layer.warehouse_code, []).append(layer)

    snapshots = []
    for wh_code, wh_layer_list in warehouse_layers.items():
        total_qty = sum(l.remaining_quantity for l in wh_layer_list)
        if total_qty == 0:
            continue

        if method in ("weighted_average", "moving_average"):
            unit_cost = calculate_weighted_average(wh_layer_list)
            total_value = unit_cost * total_qty
        elif method == "standard_cost":
            unit_cost = method_record.standard_cost or Decimal('0')
            total_value = unit_cost * total_qty
        else:
            # For FIFO/LIFO, the total value is simply sum(remaining_qty * unit_cost)
            total_value = sum(l.remaining_quantity * l.unit_cost for l in wh_layer_list)
            unit_cost = total_value / total_qty if total_qty > 0 else Decimal('0')

        snapshot = ValuationSnapshotResponse(
            id=0, # not saved yet
            snapshot_date=date.today(),
            product_code=product_code,
            warehouse_code=wh_code,
            quantity=total_qty,
            unit_cost=unit_cost,
            total_value=total_value,
            method=method,
            calculated_at=datetime.now(),
            created_at=datetime.now()
        )
        snapshots.append(snapshot)
    return snapshots


async def generate_snapshot(db: AsyncSession, snapshot_date: date | None = None) -> list[ValuationSnapshot]:
    """Generate a point-in-time valuation snapshot for all active products."""
    snapshot_date = snapshot_date or date.today()

    # Get all active products that have remaining inventory
    result = await db.execute(
        select(CostLayer.product_code, CostLayer.warehouse_code)
        .where(CostLayer.remaining_quantity > 0)
        .distinct()
    )
    product_warehouse_pairs = result.all()

    created_snapshots = []
    for product_code, warehouse_code in product_warehouse_pairs:
        try:
            # Calculate valuation for the product
            val_results = await calculate_valuation(db, product_code, warehouse_code)
            for val in val_results:
                snapshot = ValuationSnapshot(
                    snapshot_date=snapshot_date,
                    product_code=val.product_code,
                    warehouse_code=val.warehouse_code,
                    quantity=val.quantity,
                    unit_cost=val.unit_cost,
                    total_value=val.total_value,
                    method=val.method
                )
                db.add(snapshot)
                created_snapshots.append(snapshot)
        except NotFoundError:
            # Skip if no valuation method found
            pass

    await db.flush()
    return created_snapshots


async def get_valuation_report(
    db: AsyncSession, product_code: str | None = None, warehouse_code: str | None = None, category: str | None = None
) -> ValuationReport:
    """Get a valuation report filtered by product, warehouse, or category."""
    # Since category isn't in CostLayer directly, it would typically join with Product.
    # We will aggregate current CostLayers based on given filters.

    query = select(CostLayer).where(CostLayer.remaining_quantity > 0)
    if product_code:
        query = query.where(CostLayer.product_code == product_code)
    if warehouse_code:
        query = query.where(CostLayer.warehouse_code == warehouse_code)

    result = await db.execute(query)
    layers = list(result.scalars().all())

    # Group by product and warehouse
    grouped: dict[tuple[str, str], dict] = {}
    for layer in layers:
        key = (layer.product_code, layer.warehouse_code)
        if key not in grouped:
            grouped[key] = {'quantity': Decimal('0'), 'total_value': Decimal('0')}
        grouped[key]['quantity'] += layer.remaining_quantity
        grouped[key]['total_value'] += layer.remaining_quantity * layer.unit_cost

    items = []
    total_val = Decimal('0')
    for (p_code, w_code), data in grouped.items():
        items.append(ValuationReportItem(
            product_code=p_code,
            warehouse_code=w_code,
            category=category, # category filter mock
            quantity=data['quantity'],
            total_value=data['total_value']
        ))
        total_val += data['total_value']

    return ValuationReport(items=items, total_value=total_val)


async def get_valuation_summary(db: AsyncSession) -> ValuationSummary:
    """Get an aggregated valuation summary with total items, total value, by method."""

    # Needs to fetch active method per product, and sum inventory values
    query = select(
        ValuationMethod.method,
        func.count(func.distinct(CostLayer.product_code)).label("total_items"),
        func.sum(CostLayer.remaining_quantity * CostLayer.unit_cost).label("total_value")
    ).select_from(CostLayer).join(
        ValuationMethod,
        (CostLayer.product_code == ValuationMethod.product_code) & (ValuationMethod.is_active == True)
    ).where(CostLayer.remaining_quantity > 0).group_by(ValuationMethod.method)

    result = await db.execute(query)
    rows = result.all()

    by_method = []
    total_items = 0
    total_value = Decimal('0')

    for row in rows:
        method, items, value = row
        items = items or 0
        value = value or Decimal('0')
        by_method.append(ValuationSummaryItem(
            method=method,
            total_items=items,
            total_value=value
        ))
        total_items += items
        total_value += value

    return ValuationSummary(
        total_items=total_items,
        total_value=total_value,
        by_method=by_method
    )


async def get_cost_layers(
    db: AsyncSession, product_code: str | None = None, warehouse_code: str | None = None
) -> list[CostLayer]:
    """List cost layers with optional filters."""
    query = select(CostLayer)
    if product_code:
        query = query.where(CostLayer.product_code == product_code)
    if warehouse_code:
        query = query.where(CostLayer.warehouse_code == warehouse_code)

    query = query.order_by(CostLayer.received_date.asc(), CostLayer.layer_number.asc())

    result = await db.execute(query)
    return list(result.scalars().all())

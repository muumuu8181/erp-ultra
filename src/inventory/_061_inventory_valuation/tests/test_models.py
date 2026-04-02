import pytest
from datetime import date
from decimal import Decimal

from src.inventory._061_inventory_valuation.models import ValuationMethod, ValuationSnapshot, CostLayer

pytestmark = pytest.mark.asyncio

async def test_valuation_method_creation(db_session):
    method = ValuationMethod(
        product_code="TEST-01",
        method="fifo",
        effective_from=date.today(),
        is_active=True
    )
    db_session.add(method)
    await db_session.commit()

    assert method.id is not None
    assert method.product_code == "TEST-01"
    assert method.method == "fifo"
    assert method.is_active is True

async def test_valuation_snapshot_creation(db_session):
    snapshot = ValuationSnapshot(
        snapshot_date=date.today(),
        product_code="TEST-01",
        warehouse_code="WH-01",
        quantity=Decimal('10.0'),
        unit_cost=Decimal('5.5'),
        total_value=Decimal('55.0'),
        method="fifo"
    )
    db_session.add(snapshot)
    await db_session.commit()

    assert snapshot.id is not None
    assert snapshot.quantity == Decimal('10.0')

async def test_cost_layer_creation(db_session):
    layer = CostLayer(
        product_code="TEST-01",
        warehouse_code="WH-01",
        received_date=date.today(),
        quantity=Decimal('100.0'),
        remaining_quantity=Decimal('100.0'),
        unit_cost=Decimal('12.5'),
        layer_number=1
    )
    db_session.add(layer)
    await db_session.commit()

    assert layer.id is not None
    assert layer.remaining_quantity == Decimal('100.0')

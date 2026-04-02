import pytest
from datetime import date
from decimal import Decimal
import datetime

from src.inventory._061_inventory_valuation import service
from src.inventory._061_inventory_valuation.schemas import ValuationMethodCreate
from src.inventory._061_inventory_valuation.models import ValuationMethod

pytestmark = pytest.mark.asyncio

async def test_set_valuation_method(db_session):
    data1 = ValuationMethodCreate(
        product_code="TEST-PROD",
        method="fifo",
        effective_from=date.today()
    )
    method1 = await service.set_valuation_method(db_session, data1)

    data2 = ValuationMethodCreate(
        product_code="TEST-PROD",
        method="lifo",
        effective_from=date.today()
    )
    method2 = await service.set_valuation_method(db_session, data2)

    # Refresh method1
    await db_session.refresh(method1)

    assert method1.is_active is False
    assert method2.is_active is True

async def test_add_cost_layer(db_session):
    layer = await service.add_cost_layer(
        db_session,
        product_code="TEST-PROD",
        warehouse_code="WH-01",
        received_date=date.today(),
        quantity=Decimal('10.0'),
        unit_cost=Decimal('100.0')
    )
    assert layer.layer_number == 1
    assert layer.remaining_quantity == Decimal('10.0')

    layer2 = await service.add_cost_layer(
        db_session,
        product_code="TEST-PROD",
        warehouse_code="WH-01",
        received_date=date.today(),
        quantity=Decimal('20.0'),
        unit_cost=Decimal('110.0')
    )
    assert layer2.layer_number == 2

async def test_consume_cost_layer_fifo(db_session):
    await service.add_cost_layer(db_session, "FIFO-PROD", "WH-01", datetime.date(2023, 1, 1), Decimal('10'), Decimal('100'))
    await service.add_cost_layer(db_session, "FIFO-PROD", "WH-01", datetime.date(2023, 1, 2), Decimal('20'), Decimal('110'))

    consumed = await service.consume_cost_layer(db_session, "FIFO-PROD", "WH-01", Decimal('15'), "fifo")

    assert len(consumed) == 2
    assert consumed[0].quantity == Decimal('10')
    assert consumed[0].remaining_quantity == Decimal('0')
    assert consumed[1].remaining_quantity == Decimal('15')

async def test_consume_cost_layer_lifo(db_session):
    await service.add_cost_layer(db_session, "LIFO-PROD", "WH-01", datetime.date(2023, 1, 1), Decimal('10'), Decimal('100'))
    await service.add_cost_layer(db_session, "LIFO-PROD", "WH-01", datetime.date(2023, 1, 2), Decimal('20'), Decimal('110'))

    consumed = await service.consume_cost_layer(db_session, "LIFO-PROD", "WH-01", Decimal('15'), "lifo")

    assert len(consumed) == 1
    assert consumed[0].quantity == Decimal('20')
    assert consumed[0].remaining_quantity == Decimal('5')

async def test_calculate_valuation(db_session):
    await service.set_valuation_method(db_session, ValuationMethodCreate(
        product_code="VAL-PROD", method="fifo", effective_from=date.today()
    ))
    await service.add_cost_layer(db_session, "VAL-PROD", "WH-01", date.today(), Decimal('10'), Decimal('10'))
    await service.add_cost_layer(db_session, "VAL-PROD", "WH-01", date.today(), Decimal('20'), Decimal('20'))

    snapshots = await service.calculate_valuation(db_session, "VAL-PROD")

    assert len(snapshots) == 1
    assert snapshots[0].quantity == Decimal('30')
    assert snapshots[0].total_value == Decimal('500') # 10*10 + 20*20 = 100 + 400 = 500

async def test_generate_snapshot(db_session):
    await service.set_valuation_method(db_session, ValuationMethodCreate(
        product_code="SNAP-PROD", method="fifo", effective_from=date.today()
    ))
    await service.add_cost_layer(db_session, "SNAP-PROD", "WH-01", date.today(), Decimal('10'), Decimal('10'))

    snapshots = await service.generate_snapshot(db_session, date.today())

    assert len(snapshots) > 0
    assert any(s.product_code == "SNAP-PROD" for s in snapshots)

async def test_get_valuation_report_and_summary(db_session):
    await service.set_valuation_method(db_session, ValuationMethodCreate(
        product_code="REP-PROD", method="fifo", effective_from=date.today()
    ))
    await service.add_cost_layer(db_session, "REP-PROD", "WH-01", date.today(), Decimal('10'), Decimal('10'))

    report = await service.get_valuation_report(db_session, "REP-PROD")
    assert report.total_value == Decimal('100')
    assert len(report.items) == 1

    summary = await service.get_valuation_summary(db_session)
    assert summary.total_items > 0
    assert summary.total_value >= Decimal('100')

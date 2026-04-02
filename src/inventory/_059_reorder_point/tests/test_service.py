import pytest
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import patch

from shared.errors import NotFoundError, DuplicateError, ValidationError
from src.inventory._059_reorder_point import service
from src.inventory._059_reorder_point.models import ReorderPoint, ReorderAlert
from src.inventory._059_reorder_point.schemas import (
    ReorderPointCreate,
    ReorderPointUpdate,
    ReviewCycleEnum,
    AlertStatusEnum
)

pytestmark = pytest.mark.asyncio


async def test_create_reorder_point(db: AsyncSession):
    data = ReorderPointCreate(
        product_code="SRV-PROD-1",
        warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"),
        safety_stock=Decimal("20"),
        reorder_quantity=Decimal("50"),
        lead_time_days=7,
        review_cycle=ReviewCycleEnum.DAILY
    )
    rp = await service.create_reorder_point(db, data)
    assert rp.id is not None
    assert rp.product_code == "SRV-PROD-1"

    # Check duplicate
    with pytest.raises(DuplicateError):
        await service.create_reorder_point(db, data)


async def test_get_reorder_point(db: AsyncSession):
    data = ReorderPointCreate(
        product_code="SRV-PROD-GET",
        warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"),
        safety_stock=Decimal("20"),
        reorder_quantity=Decimal("50"),
        lead_time_days=7,
        review_cycle=ReviewCycleEnum.DAILY
    )
    rp = await service.create_reorder_point(db, data)

    fetched = await service.get_reorder_point(db, rp.id)
    assert fetched.id == rp.id

    with pytest.raises(NotFoundError):
        await service.get_reorder_point(db, 9999)


async def test_delete_reorder_point(db: AsyncSession):
    data = ReorderPointCreate(
        product_code="SRV-PROD-DEL",
        warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"),
        safety_stock=Decimal("20"),
        reorder_quantity=Decimal("50"),
        lead_time_days=7,
        review_cycle=ReviewCycleEnum.DAILY
    )
    rp = await service.create_reorder_point(db, data)

    await service.delete_reorder_point(db, rp.id)

    with pytest.raises(NotFoundError):
        await service.get_reorder_point(db, rp.id)

    with pytest.raises(NotFoundError):
        await service.delete_reorder_point(db, 9999)


async def test_update_reorder_point(db: AsyncSession):
    data = ReorderPointCreate(
        product_code="SRV-PROD-2",
        warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"),
        safety_stock=Decimal("20"),
        reorder_quantity=Decimal("50"),
        lead_time_days=7,
        review_cycle=ReviewCycleEnum.DAILY
    )
    rp = await service.create_reorder_point(db, data)

    update_data = ReorderPointUpdate(reorder_point=Decimal("120"), safety_stock=Decimal("30"))
    updated_rp = await service.update_reorder_point(db, rp.id, update_data)
    assert updated_rp.reorder_point == Decimal("120")
    assert updated_rp.safety_stock == Decimal("30")


async def test_list_reorder_points(db: AsyncSession):
    data1 = ReorderPointCreate(
        product_code="SRV-PROD-3", warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"), safety_stock=Decimal("20"), reorder_quantity=Decimal("50"),
        lead_time_days=7, review_cycle=ReviewCycleEnum.DAILY
    )
    data2 = ReorderPointCreate(
        product_code="SRV-PROD-4", warehouse_code="SRV-WH-2",
        reorder_point=Decimal("100"), safety_stock=Decimal("20"), reorder_quantity=Decimal("50"),
        lead_time_days=7, review_cycle=ReviewCycleEnum.DAILY
    )
    await service.create_reorder_point(db, data1)
    await service.create_reorder_point(db, data2)

    res = await service.list_reorder_points(db, warehouse_code="SRV-WH-1")
    assert len(res.items) == 1
    assert res.items[0].product_code == "SRV-PROD-3"


@patch('src.inventory._059_reorder_point.service._get_current_stock_stub', return_value=Decimal("10"))
async def test_check_and_generate_alerts(mock_stock, db: AsyncSession):
    data = ReorderPointCreate(
        product_code="SRV-PROD-5", warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"), safety_stock=Decimal("20"), reorder_quantity=Decimal("50"),
        lead_time_days=7, review_cycle=ReviewCycleEnum.DAILY
    )
    await service.create_reorder_point(db, data)

    # check_reorder_points -> generates alert because 10 < 100
    alerts = await service.check_reorder_points(db)
    assert len(alerts) >= 1

    alert = [a for a in alerts if a.product_code == "SRV-PROD-5"][0]
    assert alert.deficit == Decimal("90")
    assert alert.status == AlertStatusEnum.PENDING.value

    # Run again, shouldn't generate another alert because one is pending
    alerts_again = await service.generate_alerts(db)
    assert not any(a.product_code == "SRV-PROD-5" for a in alerts_again)


async def test_resolve_alert(db: AsyncSession):
    alert = ReorderAlert(
        product_code="SRV-PROD-6",
        warehouse_code="SRV-WH-1",
        current_stock=Decimal("10"),
        reorder_point=Decimal("50"),
        deficit=Decimal("40"),
        status=AlertStatusEnum.PENDING.value
    )
    db.add(alert)
    await db.flush()

    resolved_alert = await service.resolve_alert(db, alert.id)
    assert resolved_alert.status == AlertStatusEnum.RESOLVED.value
    assert resolved_alert.resolved_at is not None


async def test_calculate_safety_stock(db: AsyncSession):
    data = ReorderPointCreate(
        product_code="SRV-PROD-7", warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"), safety_stock=Decimal("20"), reorder_quantity=Decimal("50"),
        lead_time_days=7, review_cycle=ReviewCycleEnum.DAILY
    )
    rp = await service.create_reorder_point(db, data)

    # Using Z=1.65, sigma=10, LT=7
    ss = await service.calculate_safety_stock(db, rp.id, Decimal("10"), 7)
    assert ss == Decimal("43.655")


async def test_suggest_reorder_quantity_eoq(db: AsyncSession):
    data = ReorderPointCreate(
        product_code="SRV-PROD-8", warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"), safety_stock=Decimal("20"), reorder_quantity=Decimal("50"),
        lead_time_days=7, review_cycle=ReviewCycleEnum.DAILY
    )
    rp = await service.create_reorder_point(db, data)

    # D=1000, S=10, H=2 => EOQ=100
    suggestion = await service.suggest_reorder_quantity(
        db, rp.id, annual_demand=Decimal("1000"), ordering_cost=Decimal("10"), holding_cost_pct=Decimal("2")
    )
    assert suggestion.suggested_quantity == Decimal("100.000")
    assert "EOQ" in suggestion.rationale


async def test_suggest_reorder_quantity_fallback(db: AsyncSession):
    data = ReorderPointCreate(
        product_code="SRV-PROD-9", warehouse_code="SRV-WH-1",
        reorder_point=Decimal("100"), safety_stock=Decimal("20"), reorder_quantity=Decimal("50"),
        lead_time_days=7, review_cycle=ReviewCycleEnum.DAILY
    )
    rp = await service.create_reorder_point(db, data)

    # Missing parameters for EOQ -> fallback to fixed 50
    suggestion = await service.suggest_reorder_quantity(db, rp.id)
    assert suggestion.suggested_quantity == Decimal("50.000")
    assert "fixed" in suggestion.rationale

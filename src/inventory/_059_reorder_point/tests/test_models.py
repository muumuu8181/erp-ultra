import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from src.inventory._059_reorder_point.models import ReorderPoint, ReorderAlert
from src.inventory._059_reorder_point.schemas import ReviewCycleEnum, AlertStatusEnum

pytestmark = pytest.mark.asyncio


async def test_reorder_point_creation(db: AsyncSession):
    rp = ReorderPoint(
        product_code="PROD-001",
        warehouse_code="WH-A",
        reorder_point=Decimal("100.000"),
        safety_stock=Decimal("20.000"),
        reorder_quantity=Decimal("50.000"),
        lead_time_days=7,
        review_cycle=ReviewCycleEnum.DAILY.value,
    )
    db.add(rp)
    await db.flush()

    assert rp.id is not None
    assert rp.product_code == "PROD-001"
    assert rp.is_active is True  # default


async def test_reorder_point_unique_constraint(db: AsyncSession):
    rp1 = ReorderPoint(
        product_code="PROD-002",
        warehouse_code="WH-A",
        reorder_point=Decimal("100.000"),
        safety_stock=Decimal("20.000"),
        reorder_quantity=Decimal("50.000"),
        lead_time_days=7,
        review_cycle=ReviewCycleEnum.DAILY.value,
    )
    db.add(rp1)
    await db.flush()

    rp2 = ReorderPoint(
        product_code="PROD-002",
        warehouse_code="WH-A",
        reorder_point=Decimal("150.000"),
        safety_stock=Decimal("30.000"),
        reorder_quantity=Decimal("60.000"),
        lead_time_days=10,
        review_cycle=ReviewCycleEnum.WEEKLY.value,
    )
    db.add(rp2)

    with pytest.raises(IntegrityError):
        await db.flush()
    await db.rollback()


async def test_reorder_alert_creation(db: AsyncSession):
    alert = ReorderAlert(
        product_code="PROD-003",
        warehouse_code="WH-B",
        current_stock=Decimal("10.000"),
        reorder_point=Decimal("50.000"),
        deficit=Decimal("40.000"),
        status=AlertStatusEnum.PENDING.value
    )
    db.add(alert)
    await db.flush()

    assert alert.id is not None
    assert alert.status == "pending"
    assert alert.generated_at is not None
    assert alert.resolved_at is None

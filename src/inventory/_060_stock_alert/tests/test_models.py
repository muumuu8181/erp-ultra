import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.inventory._060_stock_alert.models import AlertRule, StockAlert


@pytest.mark.asyncio
async def test_alert_rule_creation(db_session: AsyncSession):
    rule = AlertRule(
        name="Low Stock Alert",
        alert_type="low_stock",
        threshold_value=10.0,
        threshold_operator="less_than",
        comparison_field="quantity",
        notify_users=["user1@example.com"],
    )
    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)

    assert rule.id is not None
    assert rule.name == "Low Stock Alert"
    assert rule.alert_type == "low_stock"
    assert rule.is_active is True  # default value


@pytest.mark.asyncio
async def test_stock_alert_creation(db_session: AsyncSession):
    rule = AlertRule(
        name="Low Stock Alert",
        alert_type="low_stock",
        threshold_value=10.0,
        threshold_operator="less_than",
        comparison_field="quantity",
        notify_users=["user1@example.com"],
    )
    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)

    alert = StockAlert(
        rule_id=rule.id,
        product_code="PROD-001",
        warehouse_code="WH-001",
        current_value=5.0,
        threshold_value=10.0,
        alert_type="low_stock",
        severity="warning",
        status="active",
        message="Stock is below threshold",
    )
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    assert alert.id is not None
    assert alert.rule_id == rule.id
    assert alert.product_code == "PROD-001"
    assert alert.status == "active"

    # Test relationship
    result = await db_session.execute(select(StockAlert).where(StockAlert.id == alert.id))
    fetched_alert = result.scalar_one()

    assert fetched_alert.rule_id == rule.id


@pytest.mark.asyncio
async def test_alert_rule_nullable_fields(db_session: AsyncSession):
    rule = AlertRule(
        name="Specific Product Alert",
        alert_type="high_stock",
        product_code="PROD-123",
        product_category="Electronics",
        warehouse_code="WH-NORTH",
        threshold_value=100.0,
        threshold_operator="greater_than",
        comparison_field="quantity",
        notify_users=["manager@example.com"],
    )
    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)

    assert rule.product_code == "PROD-123"
    assert rule.product_category == "Electronics"
    assert rule.warehouse_code == "WH-NORTH"

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.inventory._060_stock_alert import service
from src.inventory._060_stock_alert.schemas import (
    AlertRuleCreate,
    AlertType,
    ThresholdOperator,
    ComparisonField,
)
from src.inventory._060_stock_alert.models import AlertRule, StockAlert
from shared.errors import ValidationError


@pytest.mark.asyncio
async def test_create_and_update_rule(db_session: AsyncSession):
    data = AlertRuleCreate(
        name="Test Low Stock",
        alert_type=AlertType.low_stock,
        product_code="PROD-001",
        threshold_value=Decimal("15.0"),
        threshold_operator=ThresholdOperator.less_than,
        comparison_field=ComparisonField.quantity,
        notify_users=["test@example.com"],
    )

    # test create
    rule = await service.create_rule(db_session, data)
    assert rule.id is not None
    assert rule.name == "Test Low Stock"
    assert float(rule.threshold_value) == 15.0

    # test update
    update_data = {"threshold_value": "20.0", "name": "Updated Name"}
    updated_rule = await service.update_rule(db_session, rule.id, update_data)
    assert float(updated_rule.threshold_value) == 20.0
    assert updated_rule.name == "Updated Name"

    # test validation error on update
    with pytest.raises(ValidationError):
        await service.update_rule(db_session, rule.id, {"threshold_value": "-5.0"})


@pytest.mark.asyncio
async def test_evaluate_rules(db_session: AsyncSession):
    # Setup active rule
    rule = AlertRule(
        name="Test Rule",
        alert_type="low_stock",
        warehouse_code="WH-1",
        threshold_value=100.0,  # Ensure it triggers for tests (random is 0-50)
        threshold_operator="less_than",
        comparison_field="quantity",
        is_active=True,
        notify_users=["user@test.com"],
    )
    db_session.add(rule)
    await db_session.commit()

    alerts = await service.evaluate_rules(db_session, warehouse_code="WH-1")
    assert len(alerts) > 0
    assert alerts[0].rule_id == rule.id
    assert alerts[0].alert_type == "low_stock"
    assert alerts[0].status == "active"


@pytest.mark.asyncio
async def test_get_alerts(db_session: AsyncSession):
    alert1 = StockAlert(
        rule_id=1,
        product_code="PROD-A",
        warehouse_code="WH-1",
        current_value=5.0,
        threshold_value=10.0,
        alert_type="low_stock",
        severity="critical",
        status="active",
        message="Test alert 1",
    )
    alert2 = StockAlert(
        rule_id=2,
        product_code="PROD-B",
        warehouse_code="WH-2",
        current_value=15.0,
        threshold_value=10.0,
        alert_type="over_stock",
        severity="info",
        status="resolved",
        message="Test alert 2",
    )
    db_session.add_all([alert1, alert2])
    await db_session.commit()

    # Get all
    response = await service.get_alerts(db_session)
    assert response.total >= 2

    # Filter by status
    response_active = await service.get_alerts(db_session, status="active")
    assert len(response_active.items) == 1
    assert response_active.items[0].product_code == "PROD-A"

    # Filter by severity
    response_info = await service.get_alerts(db_session, severity="info")
    assert len(response_info.items) == 1
    assert response_info.items[0].product_code == "PROD-B"


@pytest.mark.asyncio
async def test_acknowledge_alert(db_session: AsyncSession):
    alert = StockAlert(
        rule_id=1,
        product_code="PROD-A",
        warehouse_code="WH-1",
        current_value=5.0,
        threshold_value=10.0,
        alert_type="low_stock",
        severity="critical",
        status="active",
        message="Test alert",
    )
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    ack_alert = await service.acknowledge_alert(db_session, alert.id, "john_doe")
    assert ack_alert.status == "acknowledged"
    assert ack_alert.acknowledged_by == "john_doe"
    assert ack_alert.acknowledged_at is not None


@pytest.mark.asyncio
async def test_resolve_alert(db_session: AsyncSession):
    alert = StockAlert(
        rule_id=1,
        product_code="PROD-A",
        warehouse_code="WH-1",
        current_value=5.0,
        threshold_value=10.0,
        alert_type="low_stock",
        severity="critical",
        status="active",
        message="Test alert",
    )
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    res_alert = await service.resolve_alert(db_session, alert.id)
    assert res_alert.status == "resolved"
    assert res_alert.resolved_at is not None


@pytest.mark.asyncio
async def test_get_stats(db_session: AsyncSession):
    stats = await service.get_stats(db_session)
    assert stats.count_by_type is not None
    assert stats.count_by_severity is not None


@pytest.mark.asyncio
async def test_cleanup_old_alerts(db_session: AsyncSession):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    old_alert = StockAlert(
        rule_id=1,
        product_code="PROD-A",
        warehouse_code="WH-1",
        current_value=5.0,
        threshold_value=10.0,
        alert_type="low_stock",
        severity="info",
        status="resolved",
        message="Old alert",
        resolved_at=now - timedelta(days=100)
    )
    new_alert = StockAlert(
        rule_id=2,
        product_code="PROD-B",
        warehouse_code="WH-1",
        current_value=5.0,
        threshold_value=10.0,
        alert_type="low_stock",
        severity="info",
        status="resolved",
        message="New alert",
        resolved_at=now - timedelta(days=10)
    )
    db_session.add_all([old_alert, new_alert])
    await db_session.commit()

    deleted = await service.cleanup_old_alerts(db_session, days=90)
    assert deleted >= 1

    # Verify new alert remains
    result = await db_session.execute(select(StockAlert).where(StockAlert.id == new_alert.id))
    assert result.scalar_one_or_none() is not None

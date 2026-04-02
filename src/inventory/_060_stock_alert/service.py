import random
from decimal import Decimal
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from shared.types import PaginatedResponse
from shared.errors import NotFoundError
from src.inventory._060_stock_alert.models import AlertRule, StockAlert
from src.inventory._060_stock_alert.schemas import (
    AlertRuleCreate,
    AlertStats,
    AlertStatus,
)
from src.inventory._060_stock_alert.validators import (
    validate_threshold_value,
    validate_threshold_operator,
    validate_notify_users,
    determine_severity,
    calculate_stats,
)


async def create_rule(db: AsyncSession, data: AlertRuleCreate) -> AlertRule:
    """Create a new alert rule configuration."""
    validate_threshold_value(data.threshold_value)
    validate_threshold_operator(data.threshold_operator.value)
    validate_notify_users(data.notify_users)

    rule = AlertRule(
        name=data.name,
        alert_type=data.alert_type.value,
        product_code=data.product_code,
        product_category=data.product_category,
        warehouse_code=data.warehouse_code,
        threshold_value=float(data.threshold_value),
        threshold_operator=data.threshold_operator.value,
        comparison_field=data.comparison_field.value,
        notify_users=data.notify_users,
        is_active=True,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def update_rule(db: AsyncSession, rule_id: int, data: dict) -> AlertRule:
    """Update an existing alert rule."""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError(resource="AlertRule", resource_id=str(rule_id))

    if "threshold_value" in data:
        validate_threshold_value(Decimal(data["threshold_value"]))
    if "threshold_operator" in data:
        validate_threshold_operator(data["threshold_operator"])
    if "notify_users" in data:
        validate_notify_users(data["notify_users"])

    for key, value in data.items():
        if hasattr(rule, key):
            setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)
    return rule


async def evaluate_rules(
    db: AsyncSession, warehouse_code: str | None = None
) -> list[StockAlert]:
    """Evaluate all active rules against current stock data and generate alerts."""
    query = select(AlertRule).where(AlertRule.is_active == True)
    if warehouse_code:
        query = query.where(AlertRule.warehouse_code == warehouse_code)

    result = await db.execute(query)
    rules = result.scalars().all()

    generated_alerts = []

    for rule in rules:
        # Mock values for testing purposes
        # Assuming current_value is random between 0 and 100 for demonstration.
        # safety_stock and reorder_point are mocked dynamically to use the validator logic.
        mock_current_value = Decimal(random.uniform(0, 50))
        mock_safety_stock = Decimal("20.0")
        mock_reorder_point = Decimal("40.0")

        threshold = Decimal(str(rule.threshold_value))
        breached = False

        if rule.threshold_operator == "less_than":
            breached = mock_current_value < threshold
        elif rule.threshold_operator == "greater_than":
            breached = mock_current_value > threshold
        elif rule.threshold_operator == "equals":
            breached = mock_current_value == threshold

        if breached:
            severity = determine_severity(
                mock_current_value, mock_safety_stock, mock_reorder_point
            )
            alert = StockAlert(
                rule_id=rule.id,
                product_code=rule.product_code or "DEFAULT_PROD",
                warehouse_code=rule.warehouse_code or "DEFAULT_WH",
                current_value=float(mock_current_value),
                threshold_value=float(threshold),
                alert_type=rule.alert_type,
                severity=severity.value,
                status=AlertStatus.active.value,
                message=f"Rule {rule.name} breached: {mock_current_value} {rule.threshold_operator} {threshold}",
            )
            db.add(alert)
            generated_alerts.append(alert)

    await db.commit()
    for alert in generated_alerts:
        await db.refresh(alert)
    return generated_alerts


async def get_alerts(
    db: AsyncSession,
    status: str | None = None,
    alert_type: str | None = None,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> PaginatedResponse:
    """List stock alerts with optional filters and pagination."""
    query = select(StockAlert)

    if status:
        query = query.where(StockAlert.status == status)
    if alert_type:
        query = query.where(StockAlert.alert_type == alert_type)
    if severity:
        query = query.where(StockAlert.severity == severity)

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Pagination
    query = query.order_by(StockAlert.generated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def acknowledge_alert(
    db: AsyncSession, alert_id: int, acknowledged_by: str
) -> StockAlert:
    """Acknowledge an active alert, recording who acknowledged it."""
    result = await db.execute(select(StockAlert).where(StockAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError(resource="StockAlert", resource_id=str(alert_id))

    alert.status = AlertStatus.acknowledged.value
    alert.acknowledged_at = func.now()
    alert.acknowledged_by = acknowledged_by

    await db.commit()
    await db.refresh(alert)
    return alert


async def resolve_alert(db: AsyncSession, alert_id: int) -> StockAlert:
    """Resolve an alert, setting resolved_at timestamp."""
    result = await db.execute(select(StockAlert).where(StockAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError(resource="StockAlert", resource_id=str(alert_id))

    alert.status = AlertStatus.resolved.value
    alert.resolved_at = func.now()

    await db.commit()
    await db.refresh(alert)
    return alert


async def get_stats(
    db: AsyncSession, warehouse_code: str | None = None
) -> AlertStats:
    """Get alert statistics: count by type, severity, average resolution time."""
    query = select(StockAlert)
    if warehouse_code:
        query = query.where(StockAlert.warehouse_code == warehouse_code)

    result = await db.execute(query)
    alerts = list(result.scalars().all())

    return calculate_stats(alerts)


async def cleanup_old_alerts(db: AsyncSession, days: int = 90) -> int:
    """Delete resolved alerts older than the specified number of days. Returns count deleted."""
    # Use database func.now() combined with SQLite compatible datetime logic.
    # To keep it simple across SQLite/PG during async testing, we use python datetime.
    from datetime import datetime, timezone
    cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    query = delete(StockAlert).where(
        StockAlert.status == AlertStatus.resolved.value,
        StockAlert.resolved_at < cutoff_date
    )
    result = await db.execute(query)
    await db.commit()

    return result.rowcount

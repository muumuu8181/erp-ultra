import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from shared.errors import ValidationError
from src.inventory._060_stock_alert.validators import (
    validate_threshold_value,
    validate_threshold_operator,
    validate_notify_users,
    determine_severity,
    calculate_stats,
)
from src.inventory._060_stock_alert.schemas import AlertSeverity
from src.inventory._060_stock_alert.models import StockAlert


def test_threshold_value_validation():
    # Should not raise
    validate_threshold_value(Decimal("0.0"))
    validate_threshold_value(Decimal("10.5"))

    # Should raise
    with pytest.raises(ValidationError) as exc:
        validate_threshold_value(Decimal("-1.0"))
    assert "non-negative" in str(exc.value)


def test_threshold_operator_validation():
    # Should not raise
    validate_threshold_operator("less_than")
    validate_threshold_operator("greater_than")
    validate_threshold_operator("equals")

    # Should raise
    with pytest.raises(ValidationError) as exc:
        validate_threshold_operator("invalid_op")
    assert "Invalid threshold operator" in str(exc.value)


def test_notify_users_validation():
    # Should not raise
    validate_notify_users(["user1@test.com"])
    validate_notify_users(["user1@test.com", "user2@test.com"])

    # Should raise
    with pytest.raises(ValidationError) as exc:
        validate_notify_users([])
    assert "At least one user must be specified" in str(exc.value)


def test_severity_determination():
    safety_stock = Decimal("10.0")
    reorder_point = Decimal("20.0")

    # Critical: below safety stock
    assert determine_severity(Decimal("5.0"), safety_stock, reorder_point) == AlertSeverity.critical

    # Warning: below reorder point but above/equal to safety stock
    assert determine_severity(Decimal("15.0"), safety_stock, reorder_point) == AlertSeverity.warning
    assert determine_severity(Decimal("10.0"), safety_stock, reorder_point) == AlertSeverity.warning

    # Info: above/equal to reorder point
    assert determine_severity(Decimal("25.0"), safety_stock, reorder_point) == AlertSeverity.info
    assert determine_severity(Decimal("20.0"), safety_stock, reorder_point) == AlertSeverity.info


def test_stats_calculation():
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    alerts = [
        StockAlert(
            alert_type="low_stock",
            severity="critical",
            status="resolved",
            generated_at=now - timedelta(hours=2),
            resolved_at=now
        ),
        StockAlert(
            alert_type="low_stock",
            severity="warning",
            status="resolved",
            generated_at=now - timedelta(hours=4),
            resolved_at=now
        ),
        StockAlert(
            alert_type="high_stock",
            severity="info",
            status="active",
            generated_at=now - timedelta(hours=1)
        )
    ]

    stats = calculate_stats(alerts)

    assert stats.count_by_type == {"low_stock": 2, "high_stock": 1}
    assert stats.count_by_severity == {"critical": 1, "warning": 1, "info": 1}
    # Two resolved alerts: one took 2 hours, one took 4 hours. Average = 3 hours
    assert stats.average_resolution_hours == 3.0

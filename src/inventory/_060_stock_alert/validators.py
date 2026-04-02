from decimal import Decimal
from typing import List

from shared.errors import ValidationError
from src.inventory._060_stock_alert.schemas import (
    ThresholdOperator,
    AlertSeverity,
    AlertStats,
)
from src.inventory._060_stock_alert.models import StockAlert


def validate_threshold_value(value: Decimal) -> None:
    if value < 0:
        raise ValidationError("Threshold must be non-negative", field="threshold_value")


def validate_threshold_operator(operator: str) -> None:
    try:
        ThresholdOperator(operator)
    except ValueError:
        raise ValidationError(
            f"Invalid threshold operator: {operator}", field="threshold_operator"
        )


def validate_notify_users(users: List[str]) -> None:
    if not users:
        raise ValidationError(
            "At least one user must be specified for notifications", field="notify_users"
        )


def determine_severity(
    current_value: Decimal, safety_stock: Decimal, reorder_point: Decimal
) -> AlertSeverity:
    if current_value < safety_stock:
        return AlertSeverity.critical
    if current_value < reorder_point:
        return AlertSeverity.warning
    return AlertSeverity.info


def calculate_stats(alerts: List[StockAlert]) -> AlertStats:
    count_by_type: dict[str, int] = {}
    count_by_severity: dict[str, int] = {}
    total_resolution_hours = 0.0
    resolved_count = 0

    for alert in alerts:
        # Count by type
        count_by_type[alert.alert_type] = count_by_type.get(alert.alert_type, 0) + 1

        # Count by severity
        count_by_severity[alert.severity] = count_by_severity.get(alert.severity, 0) + 1

        # Resolution time
        if alert.status == "resolved" and alert.resolved_at and alert.generated_at:
            delta = alert.resolved_at - alert.generated_at
            total_resolution_hours += delta.total_seconds() / 3600.0
            resolved_count += 1

    average_resolution_hours = (
        total_resolution_hours / resolved_count if resolved_count > 0 else 0.0
    )

    return AlertStats(
        count_by_type=count_by_type,
        count_by_severity=count_by_severity,
        average_resolution_hours=average_resolution_hours,
    )

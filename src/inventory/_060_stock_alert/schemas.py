from enum import Enum
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from shared.types import BaseSchema


class AlertType(str, Enum):
    low_stock = "low_stock"
    high_stock = "high_stock"
    expiring_lot = "expiring_lot"
    slow_moving = "slow_moving"
    over_stock = "over_stock"


class ThresholdOperator(str, Enum):
    less_than = "less_than"
    greater_than = "greater_than"
    equals = "equals"


class ComparisonField(str, Enum):
    quantity = "quantity"
    value_days_of_supply = "value_days_of_supply"


class AlertSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


class AlertRuleCreate(BaseSchema):
    name: str
    alert_type: AlertType
    product_code: Optional[str] = None
    product_category: Optional[str] = None
    warehouse_code: Optional[str] = None
    threshold_value: Decimal
    threshold_operator: ThresholdOperator
    comparison_field: ComparisonField
    notify_users: List[str]


class AlertRuleResponse(AlertRuleCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StockAlertResponse(BaseSchema):
    id: int
    rule_id: int
    product_code: str
    warehouse_code: str
    current_value: Decimal
    threshold_value: Decimal
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    message: str
    generated_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class AlertAcknowledge(BaseSchema):
    acknowledged_by: str


class AlertStats(BaseSchema):
    count_by_type: dict[str, int]
    count_by_severity: dict[str, int]
    average_resolution_hours: float

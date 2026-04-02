# Stock Alert System

Configurable, rule-based inventory monitoring module for Ultra ERP.

This module supports creating alert rules for various conditions (low stock, high stock, expiring lots, slow-moving, overstock), evaluating those rules against current data, generating alerts with severity levels, and tracking alert lifecycle through acknowledgment and resolution.

## Usage

### Define an Alert Rule
```python
from src.inventory._060_stock_alert.schemas import AlertRuleCreate, AlertType, ThresholdOperator, ComparisonField
from src.inventory._060_stock_alert.service import create_rule

# Example data
rule_data = AlertRuleCreate(
    name="Critical Low Stock - Main Warehouse",
    alert_type=AlertType.low_stock,
    warehouse_code="WH-MAIN",
    threshold_value=100.0,
    threshold_operator=ThresholdOperator.less_than,
    comparison_field=ComparisonField.quantity,
    notify_users=["warehouse_manager@example.com"]
)

rule = await create_rule(db_session, rule_data)
```

### Evaluate Rules
Evaluating rules scans current stock and generates `StockAlert` entries if thresholds are breached.

```python
from src.inventory._060_stock_alert.service import evaluate_rules

alerts = await evaluate_rules(db_session)
for alert in alerts:
    print(f"Generated Alert: {alert.severity} - {alert.message}")
```

## API Endpoints

- `POST /api/v1/stock-alert/alert-rules`: Create an alert rule
- `GET /api/v1/stock-alert/alert-rules`: List alert rules
- `PUT /api/v1/stock-alert/alert-rules/{id}`: Update an alert rule
- `POST /api/v1/stock-alert/stock-alerts/evaluate`: Evaluate all rules and generate alerts
- `GET /api/v1/stock-alert/stock-alerts`: List stock alerts with filtering & pagination
- `POST /api/v1/stock-alert/stock-alerts/{id}/acknowledge`: Acknowledge an alert
- `POST /api/v1/stock-alert/stock-alerts/{id}/resolve`: Resolve an alert
- `GET /api/v1/stock-alert/stock-alerts/stats`: Get alert statistics
- `DELETE /api/v1/stock-alert/stock-alerts/cleanup`: Cleanup old resolved alerts

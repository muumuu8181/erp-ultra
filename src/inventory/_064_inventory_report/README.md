# 064 - Inventory Report Module

This module manages Inventory Reports within Phase 3 (Inventory).

## Models
- `InventoryReport`: Inherits from `shared.types.BaseModel` and tracks inventory reporting metadata, configuration, and statuses.

## Endpoints
Prefix: `/api/v1/inventory-reports`

- `POST /` - Create a new inventory report
- `GET /{id}` - Get an inventory report
- `GET /` - List inventory reports with pagination
- `PUT /{id}` - Update an inventory report
- `DELETE /{id}` - Delete an inventory report

## Usage Example
```python
from src.inventory.064_inventory_report.schemas import InventoryReportCreate
from src.inventory.064_inventory_report.service import create_inventory_report

data = InventoryReportCreate(
    code="REP-001",
    name="Monthly Stock Level Report",
    report_type="stock_level"
)

report = await create_inventory_report(db, data)
```

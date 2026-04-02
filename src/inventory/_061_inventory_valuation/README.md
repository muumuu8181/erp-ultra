# 061 Inventory Valuation

Tracks inventory costs using multiple valuation methods (FIFO, LIFO, weighted average, standard cost, moving average).

## Usage Example

```python
from decimal import Decimal
from datetime import date
from src.inventory._061_inventory_valuation.service import set_valuation_method, add_cost_layer
from src.inventory._061_inventory_valuation.schemas import ValuationMethodCreate

# 1. Set valuation method
await set_valuation_method(db, ValuationMethodCreate(
    product_code="PROD-001",
    method="fifo",
    effective_from=date.today()
))

# 2. Add inventory layers
await add_cost_layer(
    db,
    product_code="PROD-001",
    warehouse_code="WH-MAIN",
    received_date=date.today(),
    quantity=Decimal("100"),
    unit_cost=Decimal("15.50")
)
```

## Router Prefix
`/api/v1/inventory-valuation`

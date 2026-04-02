# 038 Shipment Module

This module manages the shipment of goods, including shipment headers and line items.

## Usage Example

```python
from decimal import Decimal
from src.sales._038_shipment import (
    create_shipment,
    ShipmentCreate,
    ShipmentItemCreate
)

shipment_data = ShipmentCreate(
    sales_order_id=101,
    customer_id=5,
    status="draft",
    items=[
        ShipmentItemCreate(product_id=1, quantity=Decimal("10.0"))
    ]
)

# async with get_db() as db:
#    shipment = await create_shipment(db, shipment_data)
```

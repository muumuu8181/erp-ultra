# 049 - Promotion Campaign

This module handles the creation, management, and application of promotional campaigns for the sales system.

## Features
- Multiple promotion types: percentage off, fixed off, free gift, bundle, buy X get Y.
- Evaluating carts against active promotions to find the best savings.
- Tracking promotion redemptions.

## Example

```python
from decimal import Decimal
from datetime import date
from src.sales._049_promotion.schemas import PromotionCreate
from src.sales._049_promotion.models import PromotionType

promotion = PromotionCreate(
    code="SUMMER26",
    name="Summer Sale 2026",
    promotion_type=PromotionType.PERCENTAGE_OFF,
    value=Decimal("15.00"),
    product_codes=["PROD-123", "PROD-456"],
    customer_groups=[],
    start_date=date(2026, 6, 1),
    end_date=date(2026, 8, 31),
    is_active=True
)
```

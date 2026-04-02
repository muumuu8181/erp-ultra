# Module 044 - Discount & Promotion Rules

This module handles discount rules, automatic discount application, and usage tracking.

## Usage Example

```python
from src.sales._044_discount.schemas import DiscountRuleCreate
from src.sales._044_discount.models import DiscountType, AppliesTo

data = DiscountRuleCreate(
    name="Summer Sale 10% Off",
    code="SUMMER10",
    discount_type=DiscountType.percentage,
    value=Decimal("10.00"),
    applies_to=AppliesTo.order_total,
    start_date=date(2025, 6, 1),
    end_date=date(2025, 8, 31),
    is_stackable=True,
    is_active=True
)

# Create a rule
rule = await service.create_rule(db, data)

# Apply a discount
req = DiscountApplyRequest(...)
resp = await service.apply_discount(db, req)
```

## API Endpoints

- `POST /api/v1/discount-rules` - Create rule
- `GET /api/v1/discount-rules` - List active rules
- `PUT /api/v1/discount-rules/{id}` - Update rule
- `POST /api/v1/discounts/apply` - Apply discounts to order
- `POST /api/v1/discounts/validate` - Validate code
- `GET /api/v1/discount-rules/{id}/usage` - Usage history
- `DELETE /api/v1/discount-rules/{id}` - Deactivate rule

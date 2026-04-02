# 029_payment_terms

Payment Terms module for defining the duration allowed for payment.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/payment-terms` | List Payment Terms |
| POST | `/api/v1/payment-terms` | Create a Payment Term |
| GET | `/api/v1/payment-terms/{term_id}` | Get a specific Payment Term by ID |
| PUT | `/api/v1/payment-terms/{term_id}` | Update a Payment Term |
| DELETE | `/api/v1/payment-terms/{term_id}` | Delete a Payment Term |

## Usage

```python
from src.domain._029_payment_terms.schemas import PaymentTermCreate
from src.domain._029_payment_terms import service

# In a service or router
async def my_func(db: AsyncSession):
    # Create a payment term
    data = PaymentTermCreate(code="NET30", name="Net 30 Days", days=30)
    term = await service.create_payment_term(db, data)

    # List payment terms
    terms, total = await service.list_payment_terms(db)
```

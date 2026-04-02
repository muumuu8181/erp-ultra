# 024 Contact Management

This module manages contacts, typically associated with customers or suppliers.

## Usage Example

```python
from domain._024_contact.schemas import ContactCreate
from domain._024_contact.service import create_contact

# Create a new contact
data = ContactCreate(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    phone="+1234567890",
    customer_id=1
)
contact = await create_contact(db_session, data)
```

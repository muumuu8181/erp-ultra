# 011 Common Validators

This module provides validation capabilities for the ERP system, divided into two main categories:

1.  **Static/Reusable Validators**: Pre-defined Python functions for common data validation (e.g., Japanese phone numbers, postal codes, emails). These can be directly imported and used in Pydantic schemas or other logic across the system.
2.  **Dynamic Validation Rules**: A database-backed system for defining, updating, and evaluating validation rules at runtime (e.g., regex, ranges, specific allowed values).

## 1. Reusable Validators

You can import these directly into your module for quick validation:

```python
from src.foundation._011_validators.validators import (
    validate_japanese_phone,
    validate_postal_code,
    validate_email,
    check_japanese_phone  # Pydantic helper
)

# Usage in logic
is_valid = validate_email("test@example.com")

# Usage in Pydantic V2
from typing import Annotated
from pydantic import BaseModel, AfterValidator

class UserProfile(BaseModel):
    phone: Annotated[str, AfterValidator(check_japanese_phone)]
```

## 2. Dynamic Validation Rules (API & Service)

Dynamic rules are stored in the database (`ValidationRule` model) and can be evaluated on the fly.

### Supported Rule Types
*   `regex`: Uses the `pattern` parameter to match the value.
*   `range`: Uses `min` and `max` parameters to evaluate a numeric value.
*   `length`: Uses `min` and `max` parameters to evaluate the length of a string.
*   `in`: Uses `choices` (a list) to ensure the value is one of the allowed options.

### Service Usage

```python
from src.foundation._011_validators import service

# ... inside an async function ...
result = await service.evaluate(db_session, rule_name="strict_password", value="MySecret123!")

if not result.is_valid:
    print(f"Validation failed: {result.error_message}")
```

### API Endpoints

The module exposes a REST API to manage these rules:

*   `GET /api/v1/validators/rules`: List rules.
*   `POST /api/v1/validators/rules`: Create a rule.
*   `GET /api/v1/validators/rules/{id}`: Get a specific rule.
*   `PATCH /api/v1/validators/rules/{id}`: Update a rule.
*   `DELETE /api/v1/validators/rules/{id}`: Delete a rule.
*   `POST /api/v1/validators/evaluate`: Evaluate a value against a rule.

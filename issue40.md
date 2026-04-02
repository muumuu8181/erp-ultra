## Overview

Implement the **Quotation Management** module for the ERP system. This module handles creation, lifecycle, and conversion of sales quotations. Quotations are pre-order documents that can be sent to customers, approved, rejected, or converted into sales orders.

## Directory

```
src/sales/_036_quotation/
├── __init__.py
├── models.py
├── schemas.py
├── service.py
├── router.py
├── validators.py
├── README.md
└── tests/
    ├── test_models.py
    ├── test_service.py
    ├── test_router.py
    └── test_validators.py
```

## Module Contract

### Import Rules
```python
from shared.types import Base, BaseModel, BaseSchema, PaginatedResponse, AuditableMixin, SoftDeleteMixin, Money, Address, ContactInfo, DocumentStatus, TaxType, PaymentStatus, Priority, Quantity, DateRange, CodeGenerator
from shared.errors import NotFoundError, ValidationError, DuplicateError, BusinessRuleError, CalculationError
from shared.schema import ColLen, Precision
from src.foundation._001_database.engine import get_db
```

- ALL public functions: type hints + docstrings
- Router prefix: `/api/v1/quotations`
- Tests: pytest-asyncio
- Only import from `shared/` and `_001_database`
- Each module defines its OWN models (`customer_code`, `product_code` etc. are `String` fields, NOT foreign keys)

---

## Models (`models.py`)

### `Quotation` (table: `quotations`)

| Field                | Type                        | Constraints                          |
|----------------------|-----------------------------|--------------------------------------|
| `id`                 | Integer (PK)                | autoincrement                        |
| `quotation_number`   | String(50)                  | unique, not null                     |
| `customer_code`      | String(50)                  | not null                             |
| `customer_name`      | String(200)                 | not null                             |
| `quotation_date`     | Date                        | not null                             |
| `valid_until`        | Date                        | not null                             |
| `status`             | Enum: draft / sent / approved / rejected / expired / cancelled | not null, default=draft |
| `currency_code`      | String(3)                   | not null, default=USD                |
| `subtotal`           | Numeric(15,2)               | not null, default=0                  |
| `tax_amount`         | Numeric(15,2)               | not null, default=0                  |
| `total_amount`       | Numeric(15,2)               | not null, default=0                  |
| `notes`              | Text                        | nullable                             |
| `sales_person`       | String(100)                 | nullable                             |
| `created_by`         | String(100)                 | nullable                             |
| `created_at`         | DateTime                    | server_default=now                   |
| `updated_at`         | DateTime                    | onupdate=now                         |

- Relationship: `lines` -> `QuotationLine` (cascade delete)

### `QuotationLine` (table: `quotation_lines`)

| Field                | Type                        | Constraints                          |
|----------------------|-----------------------------|--------------------------------------|
| `id`                 | Integer (PK)                | autoincrement                        |
| `quotation_id`       | Integer (FK -> quotations)  | not null, ondelete CASCADE           |
| `line_number`        | Integer                     | not null                             |
| `product_code`       | String(50)                  | not null                             |
| `product_name`       | String(200)                 | not null                             |
| `description`        | Text                        | nullable                             |
| `quantity`           | Numeric(15,3)               | not null                             |
| `unit`               | String(20)                  | not null, default=PCS                |
| `unit_price`         | Numeric(15,2)               | not null                             |
| `discount_percentage`| Numeric(5,2)               | not null, default=0                  |
| `tax_type`           | Enum (TaxType)              | not null                             |
| `line_amount`        | Numeric(15,2)               | not null, default=0                  |
| `created_at`         | DateTime                    | server_default=now                   |
| `updated_at`         | DateTime                    | onupdate=now                         |

---

## Schemas (`schemas.py`)

- `QuotationLineCreate` - request body for a single line
- `QuotationCreate` - request body: `customer_code`, `customer_name`, `quotation_date`, `valid_until`, `currency_code`, `notes`, `sales_person`, `lines: list[QuotationLineCreate]`
- `QuotationUpdate` - partial update: all fields optional except id
- `QuotationResponse` - full response including `lines: list[QuotationLineResponse]`
- `QuotationLineResponse` - single line response
- `QuotationListFilter` - filters: `status`, `customer_code`, `date_from`, `date_to`, `page`, `page_size`

All response schemas should inherit from or use `BaseSchema` / `PaginatedResponse` where appropriate.

---

## Service (`service.py`)

Functions (all with type hints and docstrings):

```python
async def create_quotation(db: AsyncSession, data: QuotationCreate) -> Quotation
async def update_quotation(db: AsyncSession, quotation_id: int, data: QuotationUpdate) -> Quotation
async def get_quotation(db: AsyncSession, quotation_id: int) -> Quotation
async def list_quotations(db: AsyncSession, filters: QuotationListFilter) -> PaginatedResponse
async def send_quotation(db: AsyncSession, quotation_id: int) -> Quotation
async def approve_quotation(db: AsyncSession, quotation_id: int) -> Quotation
async def reject_quotation(db: AsyncSession, quotation_id: int) -> Quotation
async def expire_quotation(db: AsyncSession, quotation_id: int) -> Quotation
async def convert_to_order(db: AsyncSession, quotation_id: int) -> dict
async def calculate_totals(lines: list[QuotationLineCreate]) -> tuple[Decimal, Decimal, Decimal]
```

Business logic:
- `create_quotation`: auto-generate `quotation_number` using `CodeGenerator`, calculate totals, validate lines
- `update_quotation`: only allowed in `draft` status
- `send_quotation`: transition `draft` -> `sent`
- `approve_quotation`: transition `sent` -> `approved`
- `reject_quotation`: transition `sent` -> `rejected`
- `expire_quotation`: transition any -> `expired` (if past valid_until)
- `convert_to_order`: transition `approved` -> returns order data structure (dict) suitable for the `_037_sales_order` module; does NOT create the order itself
- `calculate_totals`: compute subtotal (sum of line amounts), tax per line based on `tax_type`, and grand total

---

## Router (`router.py`)

Prefix: `/api/v1/quotations`

| Method  | Path                           | Description                        |
|---------|--------------------------------|------------------------------------|
| POST    | `/`                            | Create quotation                   |
| GET     | `/`                            | List quotations (filtered)         |
| GET     | `/{id}`                        | Get quotation by ID                |
| PUT     | `/{id}`                        | Update quotation                   |
| POST    | `/{id}/send`                   | Send quotation (draft -> sent)     |
| POST    | `/{id}/approve`                | Approve quotation (sent -> approved)|
| POST    | `/{id}/reject`                 | Reject quotation (sent -> rejected)|
| POST    | `/{id}/convert`                | Convert to sales order data        |
| GET     | `/expired`                     | List expired quotations            |

---

## Validators (`validators.py`)

1. **`valid_until >= quotation_date`** - valid_until must be on or after quotation_date
2. **At least one line** - quotation must have at least one line item
3. **Positive quantities** - `quantity > 0` for every line
4. **Sequential line numbers** - line_number must be sequential starting from 1
5. **`customer_code` not empty** - customer_code must be a non-empty string
6. **Status transitions** - enforce valid state machine transitions (draft->sent->approved/rejected, any->expired/cancelled)
7. **Unit price non-negative** - `unit_price >= 0`
8. **Discount range** - `0 <= discount_percentage <= 100`

---

## Tests (`tests/`)

All tests use **pytest-asyncio**.

### `test_models.py`
- Test Quotation model creation with all fields
- Test QuotationLine model creation and relationship
- Test cascade delete (deleting quotation deletes lines)
- Test status enum values
- Test default values (subtotal=0, tax_amount=0, total_amount=0)

### `test_service.py`
- Test `create_quotation` with valid data
- Test `update_quotation` only works in draft status
- Test `send_quotation` transitions draft -> sent
- Test `approve_quotation` transitions sent -> approved
- Test `reject_quotation` transitions sent -> rejected
- Test `expire_quotation` sets status to expired
- Test `convert_to_order` returns correct data structure
- Test `calculate_totals` computes correct subtotal, tax, total
- Test `list_quotations` with filters (status, customer_code, date range)
- Test duplicate `quotation_number` raises `DuplicateError`
- Test invalid status transition raises `BusinessRuleError`

### `test_router.py`
- Test POST /quotations returns 201 with correct data
- Test GET /quotations returns paginated list
- Test GET /quotations/{id} returns quotation with lines
- Test PUT /quotations/{id} updates draft quotation
- Test POST /quotations/{id}/send returns updated quotation
- Test POST /quotations/{id}/approve returns updated quotation
- Test POST /quotations/{id}/convert returns order data
- Test GET /quotations/expired returns filtered list
- Test 404 for non-existent quotation

### `test_validators.py`
- Test valid_until < quotation_date raises `ValidationError`
- Test zero lines raises `ValidationError`
- Test negative quantity raises `ValidationError`
- Test non-sequential line_number raises `ValidationError`
- Test empty customer_code raises `ValidationError`
- Test invalid discount_percentage raises `ValidationError`
- Test valid data passes all validators

---

## Dependencies

- `shared.types`: Base, BaseModel, BaseSchema, PaginatedResponse, CodeGenerator, TaxType
- `shared.errors`: NotFoundError, ValidationError, DuplicateError, BusinessRuleError, CalculationError
- `shared.schema`: ColLen, Precision
- `src.foundation._001_database.engine`: get_db
- SQLAlchemy 2.0 async session
- FastAPI routing

---

## Quality Checklist

- [ ] All models use SQLAlchemy 2.0 declarative style with `Mapped` type hints
- [ ] All public functions have type hints and docstrings
- [ ] All router endpoints have proper response models
- [ ] All validators raise appropriate `shared.errors` exceptions
- [ ] Status transitions follow the defined state machine
- [ ] `quotation_number` is auto-generated and unique
- [ ] `calculate_totals` correctly computes per-line tax based on `TaxType`
- [ ] `convert_to_order` returns a clean dict (no ORM objects)
- [ ] All tests pass with `pytest-asyncio`
- [ ] No imports from other `src/sales/` modules
- [ ] No imports from `src.*` except `_001_database`

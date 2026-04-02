## Overview

Implement the Serial Number Tracking module for tracking individual serialized products throughout their lifecycle. Supports serial number registration, status management (in_stock, reserved, shipped, in_repair, scrapped), full traceability via event history, and warranty tracking.

## Directory

```
src/inventory/_056_serial_tracking/
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

## Models

### `SerialNumber` table

| Field | Type | Constraints |
|-------|------|-------------|
| id | Integer | PK, auto-increment |
| serial_number | String(100) | UNIQUE, NOT NULL |
| product_code | String(50) | NOT NULL |
| warehouse_code | String(50) | NOT NULL |
| bin_code | String(50) | nullable |
| status | Enum[in_stock, reserved, shipped, in_repair, scrapped] | NOT NULL |
| supplier_code | String(50) | nullable |
| customer_code | String(50) | nullable |
| purchase_date | Date | nullable |
| sale_date | Date | nullable |
| warranty_start | Date | nullable |
| warranty_end | Date | nullable |
| notes | Text | nullable |
| created_at | DateTime | server default |
| updated_at | DateTime | on update |

### `SerialHistory` table

| Field | Type | Constraints |
|-------|------|-------------|
| id | Integer | PK, auto-increment |
| serial_id | Integer | FK -> SerialNumber.id |
| event_type | Enum[received, stored, reserved, shipped, returned, transferred, repaired, scrapped] | NOT NULL |
| reference_type | String(50) | NOT NULL |
| reference_number | String(50) | NOT NULL |
| location_from | String(100) | nullable |
| location_to | String(100) | nullable |
| event_date | DateTime | NOT NULL |
| notes | Text | nullable |
| created_at | DateTime | server default |

## Schemas

- `SerialCreate` - serial_number, product_code, warehouse_code, bin_code?, status?, supplier_code?, customer_code?, purchase_date?, warranty_start?, warranty_end?, notes?
- `SerialResponse` - all SerialNumber fields + id, created_at, updated_at
- `SerialHistoryResponse` - id, serial_id, event_type, reference_type, reference_number, location_from, location_to, event_date, notes, created_at
- `SerialTraceRequest` - serial_number, direction: Enum[forward, backward]
- `SerialTraceResponse` - serial_number, product_code, current_status, history: list[SerialHistoryResponse]
- `WarrantyCheck` - serial_number, check_date: date
- `WarrantyCheckResponse` - serial_number, product_code, is_under_warranty, warranty_start, warranty_end, days_remaining

## Service

```python
async def register_serial(db: AsyncSession, data: SerialCreate) -> SerialNumber
    # Create serial number record, create "received" history event
async def update_status(db: AsyncSession, serial_id: int, new_status: str, reference_type: str, reference_number: str, notes: str | None) -> SerialNumber
    # Validate status transition, update status, create history event
async def reserve(db: AsyncSession, serial_id: int, reference_type: str, reference_number: str) -> SerialNumber
    # Transition: in_stock -> reserved
async def ship(db: AsyncSession, serial_id: int, customer_code: str, sale_date: date, reference_type: str, reference_number: str) -> SerialNumber
    # Transition: reserved -> shipped, set customer_code and sale_date
async def return_serial(db: AsyncSession, serial_id: int, reason: str, reference_type: str, reference_number: str) -> SerialNumber
    # Transition: shipped -> in_stock, clear customer_code
async def transfer(db: AsyncSession, serial_id: int, to_warehouse: str, to_bin: str | None, reference_number: str) -> SerialNumber
    # Update warehouse_code/bin_code, create transfer history with location_from/to
async def scrap(db: AsyncSession, serial_id: int, reason: str, reference_type: str, reference_number: str) -> SerialNumber
    # Transition: any -> scrapped
async def get_serial(db: AsyncSession, serial_id: int) -> SerialNumber
async def trace_serial(db: AsyncSession, request: SerialTraceRequest) -> SerialTraceResponse
    # Return full history for the serial number
async def check_warranty(db: AsyncSession, check: WarrantyCheck) -> WarrantyCheckResponse
    # Check if serial is under warranty on check_date
async def get_by_product(db: AsyncSession, product_code: str) -> list[SerialNumber]
async def get_by_customer(db: AsyncSession, customer_code: str) -> list[SerialNumber]
```

## Router

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/serials` | Register serial number |
| GET | `/api/v1/serials` | List serials (with filters) |
| GET | `/api/v1/serials/{id}` | Get serial detail |
| POST | `/api/v1/serials/{id}/reserve` | Reserve serial |
| POST | `/api/v1/serials/{id}/ship` | Ship serial |
| POST | `/api/v1/serials/{id}/return` | Return serial |
| POST | `/api/v1/serials/{id}/transfer` | Transfer serial |
| POST | `/api/v1/serials/{id}/scrap` | Scrap serial |
| POST | `/api/v1/serials/trace` | Trace serial history |
| POST | `/api/v1/serials/warranty-check` | Check warranty status |
| GET | `/api/v1/serials/by-product?code=` | Get serials by product |
| GET | `/api/v1/serials/by-customer?code=` | Get serials by customer |

## Validators

- `serial_number` must be unique
- Valid status transitions:
  - in_stock -> reserved, scrapped
  - reserved -> shipped, in_stock
  - shipped -> in_stock (return), in_repair
  - in_repair -> in_stock, scrapped
  - scrapped is terminal (no transitions out)
- `warranty_end` must be > `warranty_start` (if both set)
- Cannot ship without customer_code and sale_date
- Cannot scrap a serial that is already scrapped

## Tests

### test_models.py
- Test SerialNumber creation with all fields
- Test SerialHistory creation and FK relationship
- Test unique constraint on serial_number
- Test status enum values
- Test event_type enum values

### test_service.py
- Test register_serial (creates record + "received" history)
- Test update_status with valid transition
- Test update_status with invalid transition (raises BusinessRuleError)
- Test reserve (in_stock -> reserved)
- Test ship (reserved -> shipped, sets customer_code, sale_date)
- Test return_serial (shipped -> in_stock, clears customer_code)
- Test transfer (updates warehouse/bin, creates history with locations)
- Test scrap (any status -> scrapped)
- Test scrap already scrapped (raises BusinessRuleError)
- Test get_serial (found / not found)
- Test trace_serial (returns full history)
- Test check_warranty (under warranty)
- Test check_warranty (expired warranty)
- Test check_warranty (no warranty dates)
- Test get_by_product (returns filtered list)
- Test get_by_customer (returns filtered list)

### test_router.py
- Test POST /serials (201)
- Test GET /serials (200)
- Test GET /serials/{id} (200)
- Test POST /serials/{id}/reserve (200)
- Test POST /serials/{id}/ship (200)
- Test POST /serials/{id}/return (200)
- Test POST /serials/{id}/transfer (200)
- Test POST /serials/{id}/scrap (200)
- Test POST /serials/trace (200)
- Test POST /serials/warranty-check (200)
- Test GET /serials/by-product?code=XYZ (200)
- Test GET /serials/by-customer?code=CUST1 (200)

### test_validators.py
- Test serial_number uniqueness validation
- Test valid status transitions (all valid paths)
- Test invalid status transitions (raises BusinessRuleError)
- Test warranty_end > warranty_start validation
- Test ship requires customer_code and sale_date
- Test scrapped is terminal state

## Dependencies

- `shared.types`: Base, BaseModel, BaseSchema, PaginatedResponse, AuditableMixin, DateRange
- `shared.errors`: NotFoundError, ValidationError, DuplicateError, BusinessRuleError
- `shared.schema`: ColLen, Precision
- `src.foundation._001_database.engine`: get_db

## Quality Checklist

- [ ] All public functions have type hints and docstrings
- [ ] All router endpoints use `/api/v1/serials` prefix
- [ ] Tests use pytest-asyncio
- [ ] Only import from `shared/` and `_001_database`
- [ ] Every status change creates a SerialHistory event for full audit trail
- [ ] Status transitions are strictly enforced via a transition map
- [ ] Warranty check handles missing warranty dates gracefully (returns is_under_warranty=False)
- [ ] Scrap is a terminal state with no outgoing transitions
- [ ] Transfer records both location_from and location_to in history

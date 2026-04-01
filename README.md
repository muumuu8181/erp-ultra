# Ultra ERP

300K-line ERP system built with 60 parallel Jules workers.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full details.

## Module Structure

```
200 modules across 12 phases:
  Foundation (15) → Domain (20) → Sales (15) → Inventory (15)
  → Procurement (15) → Finance (20) → Management (15) → HR (20)
  → Production (15) → CRM (10) → Frontend (25) → Integration (12) + E2E (5)
```

## Tech Stack

- Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic, pytest

## Quality Standards

Every module must include:
- Full type hints on all public APIs
- Docstrings on all public functions/classes
- Tests: models, service, router, validators
- README with usage examples

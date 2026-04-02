## Overview

Implement the **Localization / i18n** module for managing multi-language support across the ERP system. Supports locale definitions, translation key-value pairs with module scoping, template-based lookup, and formatting utilities for dates, numbers, and currencies. Default locale is ja-JP with pre-seeded entries for Japanese and English.

## Directory

```
src/domain/_035_localization/
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

### Imports

```python
from shared.types import Base, BaseModel, BaseSchema, PaginatedResponse, AuditableMixin, SoftDeleteMixin, Money, Address, ContactInfo, DocumentStatus, TaxType, PaymentStatus, Priority, Quantity, DateRange, CodeGenerator
from shared.errors import NotFoundError, ValidationError, DuplicateError, BusinessRuleError
from shared.schema import ColLen, Precision
from src.foundation._001_database.engine import get_db
```

- ALL public functions: type hints + docstrings
- Router prefix: `/api/v1/localization`
- Tests: pytest-asyncio
- Only import from `shared/` and `_001_database`

---

## Models (`models.py`)

### `Locale` table

| Field            | Type                | Constraints                                  |
|------------------|---------------------|-----------------------------------------------|
| `id`             | Integer             | PK, auto-increment                           |
| `code`           | String(5)           | UNIQUE, NOT NULL (e.g. "ja-JP", "en-US")     |
| `name`           | String(100)         | NOT NULL (e.g. "日本語", "English")           |
| `language`       | String(10)          | NOT NULL (e.g. "ja", "en")                   |
| `country`        | String(10)          | NOT NULL (e.g. "JP", "US")                   |
| `date_format`    | String(20)          | NOT NULL (e.g. "%Y-%m-%d")                   |
| `number_format`  | String(20)          | NOT NULL (e.g. "#,###.##")                   |
| `currency_code`  | String(3)           | NOT NULL (e.g. "JPY", "USD")                 |
| `is_active`      | Boolean             | default True                                 |
| `created_at`     | DateTime            | server default now                           |
| `updated_at`     | DateTime            | server default now, on update now            |

### `Translation` table

| Field            | Type                | Constraints                                  |
|------------------|---------------------|-----------------------------------------------|
| `id`             | Integer             | PK, auto-increment                           |
| `locale_id`      | Integer             | FK -> Locale, NOT NULL                       |
| `module`         | String(50)          | NOT NULL                                     |
| `key`            | String(200)         | NOT NULL (format: module.section.key)        |
| `value`          | Text                | NOT NULL                                     |
| `created_at`     | DateTime            | server default now                           |
| `updated_at`     | DateTime            | server default now, on update now            |

**Indexes:**
- Unique constraint on `(locale_id, module, key)` on Translation
- Index on `locale_id` on Translation
- Index on `module` on Translation

---

## Schemas (`schemas.py`)

### `LocaleCreate` (request)
- `code`: str (max 5)
- `name`: str (max 100)
- `language`: str (max 10)
- `country`: str (max 10)
- `date_format`: str (max 20)
- `number_format`: str (max 20)
- `currency_code`: str (max 3)
- `is_active`: bool = True

### `LocaleResponse` (response)
- All fields from Locale + `id`, `created_at`, `updated_at`

### `TranslationCreate` (request)
- `locale_id`: int
- `module`: str (max 50)
- `key`: str (max 200)
- `value`: str

### `TranslationResponse` (response)
- All fields from Translation + `id`, `created_at`, `updated_at`

### `TranslationLookup` (request)
- `locale_code`: str
- `module`: str | None
- `key`: str | None

### `LocalizationExport` (response)
- `locale_code`: str
- `translations`: dict[str, str] -- key-value map of all translations

---

## Service (`service.py`)

```python
async def create_locale(db: AsyncSession, data: LocaleCreate) -> Locale:
    """Create a new locale. Validates code format (xx-XX)."""

async def list_locales(db: AsyncSession, is_active: bool | None = None) -> list[Locale]:
    """List all locales, optionally filtered by active status."""

async def add_translation(db: AsyncSession, data: TranslationCreate) -> Translation:
    """Add a translation entry. Validates key format and value not empty."""

async def get_translations(db: AsyncSession, locale_code: str, module: str | None = None) -> list[Translation]:
    """Get translations for a locale, optionally filtered by module."""

async def get_translations_by_module(db: AsyncSession, locale_code: str, module: str) -> dict[str, str]:
    """Get translations as a key-value dict for a specific locale and module."""

async def translate(db: AsyncSession, locale_code: str, key: str, default: str | None = None) -> str:
    """Look up a single translation by key. Returns default or key if not found."""

async def format_date(db: AsyncSession, locale_code: str, value: date) -> str:
    """Format a date according to locale settings."""

async def format_number(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a number according to locale settings (thousands separator, decimal)."""

async def format_currency(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a currency value according to locale settings (symbol, decimals)."""

async def export_translations(db: AsyncSession, locale_code: str, module: str | None = None) -> LocalizationExport:
    """Export translations as JSON-serializable dict."""

async def import_translations(db: AsyncSession, locale_code: str, data: dict[str, str], module: str) -> int:
    """Import translations from a key-value dict. Upserts existing entries.
    Returns count of imported/updated translations.
    """
```

---

## Router (`router.py`)

Prefix: `/api/v1/localization`

| Method   | Path                                       | Description                        |
|----------|--------------------------------------------|------------------------------------|
| POST     | `/locales`                                 | Create a locale                    |
| GET      | `/locales`                                 | List locales                       |
| POST     | `/translations`                            | Add a translation                  |
| GET      | `/translations`                            | Get translations (query: locale, module) |
| POST     | `/translations/lookup`                     | Look up a translation              |
| POST     | `/localization/format-date`                | Format a date                      |
| POST     | `/localization/format-number`              | Format a number                    |
| POST     | `/localization/format-currency`            | Format a currency value            |
| POST     | `/translations/export`                     | Export translations as JSON        |
| POST     | `/translations/import`                     | Import translations from JSON      |

**Notes:**
- GET `/translations?locale=ja-JP&module=invoice` returns list of translations
- POST `/translations/lookup` body: `{ "locale_code": "ja-JP", "key": "invoice.title", "default": "Invoice" }`
- POST `/localization/format-date` body: `{ "locale_code": "ja-JP", "value": "2025-01-15" }`
- POST `/localization/format-number` body: `{ "locale_code": "ja-JP", "value": 1234567.89 }`
- POST `/localization/format-currency` body: `{ "locale_code": "ja-JP", "value": 100000 }`
- POST `/translations/export` body: `{ "locale_code": "ja-JP", "module": "invoice" }`
- POST `/translations/import` body: `{ "locale_code": "ja-JP", "module": "invoice", "translations": { "invoice.title": "請求書", ... } }`

---

## Validators (`validators.py`)

1. **Locale code format**: must match pattern `^[a-z]{2}-[A-Z]{2}$` (e.g. "ja-JP", "en-US").
2. **Key format**: must match pattern `^[a-z_]+\.[a-z_]+\.[a-z_]+$` (module.section.key, lowercase with underscores).
3. **Value not empty**: translation value must be a non-empty string.
4. **Locale code unique**: `code` must be unique in Locale table.
5. **Translation unique per locale+module+key**: the combination `(locale_id, module, key)` must be unique.
6. **Currency code**: must be a valid 3-letter ISO 4217 code.

---

## Tests (`tests/`)

### `test_models.py`
- Locale table creation, unique code constraint
- Translation table creation, FK to Locale
- Unique constraint on (locale_id, module, key)
- Enum/index verification

### `test_service.py`
- create_locale success
- create_locale with invalid code format raises ValidationError
- create_locale with duplicate code raises DuplicateError
- list_locales with active filter
- add_translation success
- add_translation with invalid key format raises ValidationError
- add_translation with empty value raises ValidationError
- get_translations for a locale
- get_translations filtered by module
- get_translations_by_module returns dict
- translate returns value for existing key
- translate returns default for missing key
- translate returns key itself when no default
- format_date with ja-JP locale
- format_date with en-US locale
- format_number with locale-specific formatting
- format_currency with locale-specific formatting
- export_translations returns correct structure
- import_translations creates new entries
- import_translations updates existing entries (upsert)

### `test_router.py`
- POST /locales 201
- GET /locales 200
- POST /translations 201
- GET /translations?locale=ja-JP 200
- POST /translations/lookup 200
- POST /localization/format-date 200
- POST /localization/format-number 200
- POST /localization/format-currency 200
- POST /translations/export 200
- POST /translations/import 200
- Validation errors return 422

### `test_validators.py`
- Locale code format pass (ja-JP) / fail (japanese, JA-jp, jJP)
- Key format pass (invoice.title.main) / fail (Invoice, invoice.title, INV.TITLE.MAIN)
- Value not empty check
- Currency code validation

---

## Pre-seed Data

On module initialization (or via a migration/seed script), insert the following default locales:

**ja-JP (日本語):**
- code: "ja-JP", name: "日本語", language: "ja", country: "JP"
- date_format: "%Y年%m月%d日"
- number_format: "#,###"
- currency_code: "JPY"

**en-US (English):**
- code: "en-US", name: "English", language: "en", country: "US"
- date_format: "%m/%d/%Y"
- number_format: "#,###.##"
- currency_code: "USD"

---

## Dependencies

- SQLAlchemy 2.0 (async session)
- FastAPI router
- Pydantic v2 schemas
- `re` (stdlib) for format validation
- `locale` (stdlib) for formatting hints
- shared.types, shared.errors, shared.schema

---

## Quality Checklist

- [ ] All model fields match specification exactly
- [ ] Default locale is ja-JP
- [ ] Pre-seed data for ja-JP and en-US
- [ ] All service functions have type hints and docstrings
- [ ] All router endpoints return correct HTTP status codes
- [ ] Validators raise appropriate custom errors
- [ ] Tests cover happy path and all error cases
- [ ] No imports outside of `shared/` and `_001_database` (except stdlib)
- [ ] Router prefix is `/api/v1/localization`
- [ ] `pytest-asyncio` used for all tests
- [ ] `__init__.py` exports router
- [ ] Import/export works with JSON format
- [ ] Upsert behavior on import is correct

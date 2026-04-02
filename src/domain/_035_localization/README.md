# Localization / i18n Module (035)

This module handles:
- Locales configuration (country, language, formatting preferences)
- Translations mapping for the entire ERP
- Utilities to format dates, numbers, and currencies according to user locales

## Dependencies
- Phase 0: `_001_database` (engine, sessions)
- `shared.types`, `shared.errors`

## Usage Example

```python
# Look up a translation
title = await translate(db, locale_code="ja-JP", key="invoice.title.main", default="Invoice")

# Format currency
amount_str = await format_currency(db, locale_code="en-US", value=1234.56)
# "$1,234.56"
```

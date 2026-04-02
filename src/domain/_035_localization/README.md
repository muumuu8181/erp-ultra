# Localization / i18n (035)

This module provides multi-language support across the ERP system. It supports locale definitions, translation key-value pairs with module scoping, template-based lookup, and formatting utilities for dates, numbers, and currencies.

## Features

- **Locales**: Manage locales (`ja-JP`, `en-US`, etc.) and their formatting rules.
- **Translations**: Key-value pairs grouped by module (`invoice.title`).
- **Formatting**: Format dates, numbers, and currencies according to locale rules.
- **Import/Export**: Easily manage translation files.

## API Endpoints

All endpoints are prefixed with `/api/v1/localization`.

- `POST /locales` - Create a locale.
- `GET /locales` - List locales.
- `POST /translations` - Add a single translation entry.
- `GET /translations` - Get translations for a specific locale (and optional module).
- `POST /translations/lookup` - Look up a translation by key.
- `POST /localization/format-date` - Format a date according to a locale.
- `POST /localization/format-number` - Format a number according to a locale.
- `POST /localization/format-currency` - Format currency according to a locale.
- `POST /translations/export` - Export translations as a JSON-serializable map.
- `POST /translations/import` - Import and upsert translations from a JSON map.

## Usage Example

```python
from fastapi import APIRouter
from src.domain._035_localization import router as localization_router

app.include_router(localization_router)
```

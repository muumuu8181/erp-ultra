# 035_localization

Localization and i18n management for Ultra ERP.

## Features

- Locale management (code, date/number/currency format)
- Translation table with module scopes
- API endpoints for formatters and localization lookups
- Bulk import and export translations for tools

## Usage

Include router:

```python
from fastapi import FastAPI
from src.domain._035_localization import router as loc_router

app = FastAPI()
app.include_router(loc_router)
```

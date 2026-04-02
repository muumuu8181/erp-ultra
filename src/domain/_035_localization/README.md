# Localization / i18n Module (035)

This module handles multi-language support across the ERP system.

## Features
- Locale management
- Translation key-value store per module
- Template-based lookup
- Formatting utilities for dates, numbers, and currencies

## Usage
```python
from src.domain._035_localization.service import format_date, format_number, format_currency

# Format examples
formatted_date = await format_date(db, "ja-JP", date.today())
formatted_num = await format_number(db, "en-US", 1000.5)
```

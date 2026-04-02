"""
035_localization - Localization and i18n management.

Provides:
- Locale models and endpoints
- Translation entries with module/key lookup
- Formatting utils for date, number, currency
"""

from src.domain._035_localization.router import router

__all__ = ["router"]

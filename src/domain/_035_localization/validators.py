import re
from typing import Optional

from shared.errors import ValidationError


def validate_locale_code(code: str) -> None:
    """Validate locale code format (e.g., ja-JP)."""
    if not re.match(r"^[a-z]{2}-[A-Z]{2}$", code):
        raise ValidationError(f"Invalid locale code format: {code}. Expected format like 'ja-JP'.")


def validate_translation_key(key: str) -> None:
    """Validate translation key format (module.section.key)."""
    if not re.match(r"^[a-z_]+\.[a-z_]+\.[a-z_]+$", key):
        raise ValidationError(f"Invalid translation key format: {key}. Expected format like 'module.section.key'.")


def validate_translation_value(value: str) -> None:
    """Validate translation value is not empty."""
    if not value or not value.strip():
        raise ValidationError("Translation value cannot be empty.")


def validate_currency_code(code: str) -> None:
    """Validate currency code is a 3-letter ISO 4217 code."""
    if not re.match(r"^[A-Z]{3}$", str(code)):
        raise ValidationError(f"Invalid currency code format: {code}. Expected a 3-letter ISO 4217 code.")

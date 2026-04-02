import re

from shared.errors import ValidationError


def validate_locale_code(code: str) -> None:
    """Validates the locale code matches the format xx-XX."""
    if not re.match(r"^[a-z]{2}-[A-Z]{2}$", code):
        raise ValidationError("Invalid locale code format. Must match ^[a-z]{2}-[A-Z]{2}$ (e.g., 'ja-JP').")


def validate_translation_key(key: str) -> None:
    """Validates the translation key matches the format module.section.key."""
    if not re.match(r"^[a-z_]+\.[a-z_]+\.[a-z_]+$", key):
        raise ValidationError(r"Invalid translation key format. Must match ^[a-z_]+\.[a-z_]+\.[a-z_]+$")


def validate_translation_value(value: str) -> None:
    """Validates the translation value is not empty."""
    if not value or not value.strip():
        raise ValidationError("Translation value cannot be empty.")


def validate_currency_code(code: str) -> None:
    """Validates the currency code is a 3-letter ISO 4217 code."""
    if not re.match(r"^[A-Z]{3}$", code):
        raise ValidationError("Invalid currency code format. Must be a 3-letter ISO 4217 code.")

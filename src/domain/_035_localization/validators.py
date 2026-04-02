import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import ValidationError, DuplicateError
from src.domain._035_localization.models import Locale, Translation


def validate_locale_code_format(code: str) -> None:
    """Validate locale code matches xx-XX pattern."""
    if not re.match(r"^[a-z]{2}-[A-Z]{2}$", code):
        raise ValidationError(f"Invalid locale code format: {code}. Must be xx-XX.")


def validate_key_format(key: str) -> None:
    """Validate key matches module.section.key pattern (lowercase with underscores)."""
    if not re.match(r"^[a-z_]+\.[a-z_]+\.[a-z_]+$", key):
        raise ValidationError(f"Invalid key format: {key}. Must be module.section.key.")


def validate_value_not_empty(value: str) -> None:
    """Validate translation value is not empty."""
    if not value or not value.strip():
        raise ValidationError("Translation value cannot be empty.")


def validate_currency_code(code: str) -> None:
    """Validate currency code is a 3-letter ISO 4217 code."""
    if not re.match(r"^[A-Z]{3}$", code):
        raise ValidationError(f"Invalid currency code format: {code}. Must be 3 uppercase letters.")


async def validate_locale_code_unique(db: AsyncSession, code: str) -> None:
    """Check if locale code is unique in the database."""
    stmt = select(Locale).where(Locale.code == code)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise DuplicateError(f"Locale with code '{code}' already exists.")


async def validate_translation_unique(db: AsyncSession, locale_id: int, module: str, key: str) -> None:
    """Check if the combination of locale_id, module, and key is unique."""
    stmt = select(Translation).where(
        Translation.locale_id == locale_id,
        Translation.module == module,
        Translation.key == key
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise DuplicateError(f"Translation for '{key}' in module '{module}' already exists for this locale.")

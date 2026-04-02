"""
Validators for the Localization / i18n module.
"""
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.errors import ValidationError, DuplicateError

from src.domain._035_localization.models import Locale, Translation


LOCALE_CODE_PATTERN = re.compile(r"^[a-z]{2}-[A-Z]{2}$")
KEY_FORMAT_PATTERN = re.compile(r"^[a-z_]+\.[a-z_]+\.[a-z_]+$")
CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


def validate_locale_code_format(code: str) -> None:
    """Validate locale code matches xx-XX format."""
    if not LOCALE_CODE_PATTERN.match(code):
        raise ValidationError("Invalid locale code format. Expected xx-XX (e.g. ja-JP)", field="code")


def validate_key_format(key: str) -> None:
    """Validate translation key matches module.section.key format."""
    if not KEY_FORMAT_PATTERN.match(key):
        raise ValidationError("Invalid key format. Expected module.section.key (lowercase, underscores)", field="key")


def validate_value_not_empty(value: str) -> None:
    """Validate translation value is not empty."""
    if not value or not str(value).strip():
        raise ValidationError("Translation value cannot be empty", field="value")


def validate_currency_code(currency_code: str) -> None:
    """Validate currency code is a 3-letter ISO code."""
    if not CURRENCY_CODE_PATTERN.match(currency_code):
        raise ValidationError("Invalid currency code. Expected 3 uppercase letters (e.g. JPY, USD)", field="currency_code")


async def validate_locale_code_unique(db: AsyncSession, code: str) -> None:
    """Validate locale code is unique in the database."""
    result = await db.execute(select(Locale).filter(Locale.code == code))
    if result.scalars().first() is not None:
        raise DuplicateError("Locale", key=code)


async def validate_translation_unique(db: AsyncSession, locale_id: int, module: str, key: str) -> None:
    """Validate (locale_id, module, key) combination is unique."""
    result = await db.execute(
        select(Translation).filter(
            Translation.locale_id == locale_id,
            Translation.module == module,
            Translation.key == key
        )
    )
    if result.scalars().first() is not None:
        raise DuplicateError("Translation", key=f"{locale_id}-{module}-{key}")

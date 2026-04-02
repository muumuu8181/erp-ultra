"""
Service layer for the Localization / i18n module.
"""
from typing import Dict, List, Optional
from datetime import date
import locale as stdlib_locale

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError, ValidationError, DuplicateError
from src.domain._035_localization.models import Locale, Translation
from src.domain._035_localization.schemas import LocaleCreate, TranslationCreate, LocalizationExport
from src.domain._035_localization.validators import (
    validate_locale_code_format,
    validate_key_format,
    validate_value_not_empty,
    validate_currency_code,
    validate_locale_code_unique,
    validate_translation_unique,
)


async def create_locale(db: AsyncSession, data: LocaleCreate) -> Locale:
    """Create a new locale. Validates code format (xx-XX)."""
    validate_locale_code_format(data.code)
    validate_currency_code(data.currency_code)
    await validate_locale_code_unique(db, data.code)

    locale_obj = Locale(**data.model_dump())
    db.add(locale_obj)
    await db.commit()
    await db.refresh(locale_obj)
    return locale_obj


async def list_locales(db: AsyncSession, is_active: Optional[bool] = None) -> List[Locale]:
    """List all locales, optionally filtered by active status."""
    stmt = select(Locale)
    if is_active is not None:
        stmt = stmt.filter(Locale.is_active == is_active)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_translation(db: AsyncSession, data: TranslationCreate) -> Translation:
    """Add a translation entry. Validates key format and value not empty."""
    validate_key_format(data.key)
    validate_value_not_empty(data.value)

    # Ensure locale exists
    result = await db.execute(select(Locale).filter(Locale.id == data.locale_id))
    if not result.scalars().first():
        raise NotFoundError("Locale", resource_id=str(data.locale_id))

    await validate_translation_unique(db, data.locale_id, data.module, data.key)

    translation_obj = Translation(**data.model_dump())
    db.add(translation_obj)
    await db.commit()
    await db.refresh(translation_obj)
    return translation_obj


async def get_translations(db: AsyncSession, locale_code: str, module: Optional[str] = None) -> List[Translation]:
    """Get translations for a locale, optionally filtered by module."""
    locale_res = await db.execute(select(Locale).filter(Locale.code == locale_code))
    locale_obj = locale_res.scalars().first()
    if not locale_obj:
        raise NotFoundError("Locale", resource_id=locale_code)

    stmt = select(Translation).filter(Translation.locale_id == locale_obj.id)
    if module:
        stmt = stmt.filter(Translation.module == module)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_translations_by_module(db: AsyncSession, locale_code: str, module: str) -> Dict[str, str]:
    """Get translations as a key-value dict for a specific locale and module."""
    translations = await get_translations(db, locale_code, module)
    return {t.key: t.value for t in translations}


async def translate(db: AsyncSession, locale_code: str, key: str, default: Optional[str] = None) -> str:
    """Look up a single translation by key. Returns default or key if not found."""
    locale_res = await db.execute(select(Locale).filter(Locale.code == locale_code))
    locale_obj = locale_res.scalars().first()
    if not locale_obj:
        return default if default is not None else key

    result = await db.execute(select(Translation).filter(
        Translation.locale_id == locale_obj.id,
        Translation.key == key
    ))
    translation_obj = result.scalars().first()

    if translation_obj:
        return translation_obj.value

    return default if default is not None else key


async def _get_locale_by_code(db: AsyncSession, code: str) -> Locale:
    result = await db.execute(select(Locale).filter(Locale.code == code))
    locale_obj = result.scalars().first()
    if not locale_obj:
        raise NotFoundError("Locale", resource_id=code)
    return locale_obj


async def format_date(db: AsyncSession, locale_code: str, value: date) -> str:
    """Format a date according to locale settings."""
    locale_obj = await _get_locale_by_code(db, locale_code)
    return value.strftime(locale_obj.date_format)


async def format_number(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a number according to locale settings (thousands separator, decimal)."""
    locale_obj = await _get_locale_by_code(db, locale_code)
    fmt = locale_obj.number_format

    # We will implement basic custom formatting or fallback
    # The requirement specifically mentions support for "#,###.##" (en-US) or "#,###" (ja-JP)
    # A simple approach for these specific string patterns:

    if "." in fmt:
        parts = fmt.split(".")
        decimal_places = len(parts[1]) if parts[1] else 0
    else:
        decimal_places = 0

    if "#,###" in fmt:
        return f"{value:,.{decimal_places}f}"

    # default python fallback
    return f"{value:.{decimal_places}f}"


async def format_currency(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a currency value according to locale settings (symbol, decimals)."""
    locale_obj = await _get_locale_by_code(db, locale_code)

    number_str = await format_number(db, locale_code, value)

    # Add currency code. If ja-JP -> ¥, en-US -> $ (simplified logic for standard cases)
    # The requirement just says "according to locale settings".
    # For a robust implementation, we map currency code to symbols
    symbol_map = {
        "JPY": "¥",
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    symbol = symbol_map.get(locale_obj.currency_code, locale_obj.currency_code + " ")

    if locale_obj.currency_code == "JPY":
        return f"{symbol}{number_str}"
    elif locale_obj.currency_code == "USD":
        return f"{symbol}{number_str}"

    return f"{symbol}{number_str}"


async def export_translations(db: AsyncSession, locale_code: str, module: Optional[str] = None) -> LocalizationExport:
    """Export translations as JSON-serializable dict."""
    translations_list = await get_translations(db, locale_code, module)
    translations_dict = {t.key: t.value for t in translations_list}
    return LocalizationExport(locale_code=locale_code, translations=translations_dict)


async def import_translations(db: AsyncSession, locale_code: str, data: Dict[str, str], module: str) -> int:
    """Import translations from a key-value dict. Upserts existing entries.
    Returns count of imported/updated translations.
    """
    locale_obj = await _get_locale_by_code(db, locale_code)

    count = 0
    for key, value in data.items():
        validate_key_format(key)
        validate_value_not_empty(value)

        result = await db.execute(select(Translation).filter(
            Translation.locale_id == locale_obj.id,
            Translation.module == module,
            Translation.key == key
        ))
        existing_translation = result.scalars().first()

        if existing_translation:
            if existing_translation.value != value:
                existing_translation.value = value
                count += 1
        else:
            new_translation = Translation(
                locale_id=locale_obj.id,
                module=module,
                key=key,
                value=value
            )
            db.add(new_translation)
            count += 1

    await db.commit()
    return count

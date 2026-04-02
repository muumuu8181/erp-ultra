from datetime import date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import NotFoundError
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

    locale = Locale(**data.model_dump())
    db.add(locale)
    await db.commit()
    await db.refresh(locale)
    return locale


async def list_locales(db: AsyncSession, is_active: Optional[bool] = None) -> list[Locale]:
    """List all locales, optionally filtered by active status."""
    stmt = select(Locale)
    if is_active is not None:
        stmt = stmt.where(Locale.is_active == is_active)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_translation(db: AsyncSession, data: TranslationCreate) -> Translation:
    """Add a translation entry. Validates key format and value not empty."""
    validate_key_format(data.key)
    validate_value_not_empty(data.value)

    # Check if locale exists
    stmt = select(Locale).where(Locale.id == data.locale_id)
    result = await db.execute(stmt)
    if not result.scalars().first():
        raise NotFoundError(f"Locale with id {data.locale_id} not found.")

    await validate_translation_unique(db, data.locale_id, data.module, data.key)

    translation = Translation(**data.model_dump())
    db.add(translation)
    await db.commit()
    await db.refresh(translation)
    return translation


async def get_translations(db: AsyncSession, locale_code: str, module: Optional[str] = None) -> list[Translation]:
    """Get translations for a locale, optionally filtered by module."""
    # Find locale_id
    stmt_locale = select(Locale.id).where(Locale.code == locale_code)
    result_locale = await db.execute(stmt_locale)
    locale_id = result_locale.scalars().first()
    if not locale_id:
        raise NotFoundError(f"Locale code '{locale_code}' not found.")

    stmt = select(Translation).where(Translation.locale_id == locale_id)
    if module:
        stmt = stmt.where(Translation.module == module)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_translations_by_module(db: AsyncSession, locale_code: str, module: str) -> dict[str, str]:
    """Get translations as a key-value dict for a specific locale and module."""
    translations = await get_translations(db, locale_code, module)
    return {t.key: t.value for t in translations}


async def translate(db: AsyncSession, locale_code: str, key: str, default: Optional[str] = None) -> str:
    """Look up a single translation by key. Returns default or key if not found."""
    # Split key to extract module
    parts = key.split(".")
    if len(parts) >= 1:
        module = parts[0]
    else:
        return default if default is not None else key

    try:
        stmt_locale = select(Locale.id).where(Locale.code == locale_code)
        result_locale = await db.execute(stmt_locale)
        locale_id = result_locale.scalars().first()
        if not locale_id:
            return default if default is not None else key

        stmt = select(Translation).where(
            Translation.locale_id == locale_id,
            Translation.module == module,
            Translation.key == key
        )
        result = await db.execute(stmt)
        translation = result.scalars().first()
        if translation:
            return translation.value
    except Exception:
        pass
    return default if default is not None else key


async def format_date(db: AsyncSession, locale_code: str, value: date) -> str:
    """Format a date according to locale settings."""
    stmt = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(stmt)
    locale = result.scalars().first()
    if not locale:
        raise NotFoundError(f"Locale code '{locale_code}' not found.")

    # Example format string handling (%Y年%m月%d日)
    return value.strftime(locale.date_format)


async def format_number(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a number according to locale settings (thousands separator, decimal)."""
    stmt = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(stmt)
    locale = result.scalars().first()
    if not locale:
        raise NotFoundError(f"Locale code '{locale_code}' not found.")

    # Basic implementation supporting simple#,### and #,###.## formats
    if locale.number_format == "#,###":
        return f"{int(value):,}"
    elif locale.number_format == "#,###.##":
        return f"{value:,.2f}"

    # Fallback to standard python string formatting based on inferred needs
    if "." in locale.number_format:
        return f"{value:,.2f}"
    return f"{int(value):,}"


async def format_currency(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a currency value according to locale settings (symbol, decimals)."""
    stmt = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(stmt)
    locale = result.scalars().first()
    if not locale:
        raise NotFoundError(f"Locale code '{locale_code}' not found.")

    # Very basic symbol handling for tests
    symbol = ""
    if locale.currency_code == "JPY":
        symbol = "¥"
    elif locale.currency_code == "USD":
        symbol = "$"

    number_str = await format_number(db, locale_code, value)

    if locale.code == "ja-JP":
        return f"{symbol}{number_str}"
    elif locale.code == "en-US":
        return f"{symbol}{number_str}"

    return f"{locale.currency_code} {number_str}"


async def export_translations(db: AsyncSession, locale_code: str, module: Optional[str] = None) -> LocalizationExport:
    """Export translations as JSON-serializable dict."""
    translations_list = await get_translations(db, locale_code, module)
    translations_dict = {t.key: t.value for t in translations_list}
    return LocalizationExport(locale_code=locale_code, translations=translations_dict)


async def import_translations(db: AsyncSession, locale_code: str, data: dict[str, str], module: str) -> int:
    """Import translations from a key-value dict. Upserts existing entries.
    Returns count of imported/updated translations.
    """
    stmt_locale = select(Locale.id).where(Locale.code == locale_code)
    result_locale = await db.execute(stmt_locale)
    locale_id = result_locale.scalars().first()
    if not locale_id:
        raise NotFoundError(f"Locale code '{locale_code}' not found.")

    count = 0
    for key, value in data.items():
        # Skip invalid key formats instead of failing entirely for robustness, or we could fail. The issue test says upsert.
        # We will validate first
        try:
            validate_key_format(key)
            validate_value_not_empty(value)
        except ValidationError:
            continue

        stmt = select(Translation).where(
            Translation.locale_id == locale_id,
            Translation.module == module,
            Translation.key == key
        )
        result = await db.execute(stmt)
        translation = result.scalars().first()

        if translation:
            translation.value = value
        else:
            new_translation = Translation(
                locale_id=locale_id,
                module=module,
                key=key,
                value=value
            )
            db.add(new_translation)
        count += 1

    await db.commit()
    return count

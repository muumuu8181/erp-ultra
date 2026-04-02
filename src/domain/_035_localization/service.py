from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from shared.errors import NotFoundError, DuplicateError
from src.domain._035_localization.models import Locale, Translation
from src.domain._035_localization.schemas import LocaleCreate, TranslationCreate, LocalizationExport
from src.domain._035_localization.validators import (
    validate_locale_code,
    validate_currency_code,
    validate_translation_key,
    validate_translation_value
)


async def create_locale(db: AsyncSession, data: LocaleCreate) -> Locale:
    """Create a new locale. Validates code format (xx-XX)."""
    validate_locale_code(data.code)
    validate_currency_code(data.currency_code)

    query = select(Locale).where(Locale.code == data.code)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise DuplicateError(f"Locale with code '{data.code}' already exists.")

    locale = Locale(**data.model_dump())
    db.add(locale)
    try:
        await db.commit()
        await db.refresh(locale)
    except IntegrityError:
        await db.rollback()
        raise DuplicateError(f"Locale with code '{data.code}' already exists.")

    return locale


async def list_locales(db: AsyncSession, is_active: bool | None = None) -> list[Locale]:
    """List all locales, optionally filtered by active status."""
    query = select(Locale)
    if is_active is not None:
        query = query.where(Locale.is_active == is_active)
    result = await db.execute(query)
    return list(result.scalars().all())


async def add_translation(db: AsyncSession, data: TranslationCreate) -> Translation:
    """Add a translation entry. Validates key format and value not empty."""
    validate_translation_key(data.key)
    validate_translation_value(data.value)

    query = select(Translation).where(
        Translation.locale_id == data.locale_id,
        Translation.module == data.module,
        Translation.key == data.key
    )
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise DuplicateError(f"Translation with key '{data.key}' already exists for this locale and module.")

    translation = Translation(**data.model_dump())
    db.add(translation)
    try:
        await db.commit()
        await db.refresh(translation)
    except IntegrityError:
        await db.rollback()
        raise DuplicateError(f"Translation with key '{data.key}' already exists for this locale and module.")

    return translation


async def get_translations(db: AsyncSession, locale_code: str, module: str | None = None) -> list[Translation]:
    """Get translations for a locale, optionally filtered by module."""
    locale_query = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(locale_query)
    locale = result.scalar_one_or_none()
    if not locale:
        raise NotFoundError(f"Locale '{locale_code}' not found.")

    query = select(Translation).where(Translation.locale_id == locale.id)
    if module:
        query = query.where(Translation.module == module)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_translations_by_module(db: AsyncSession, locale_code: str, module: str) -> dict[str, str]:
    """Get translations as a key-value dict for a specific locale and module."""
    translations = await get_translations(db, locale_code, module)
    return {t.key: t.value for t in translations}


async def translate(db: AsyncSession, locale_code: str, key: str, default: str | None = None) -> str:
    """Look up a single translation by key. Returns default or key if not found."""
    locale_query = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(locale_query)
    locale = result.scalar_one_or_none()
    if not locale:
        return default if default is not None else key

    module = key.split('.')[0] if '.' in key else ''

    query = select(Translation).where(
        Translation.locale_id == locale.id,
        Translation.module == module,
        Translation.key == key
    )
    result = await db.execute(query)
    translation = result.scalar_one_or_none()

    if translation:
        return translation.value
    return default if default is not None else key


async def format_date(db: AsyncSession, locale_code: str, value: date) -> str:
    """Format a date according to locale settings."""
    locale_query = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(locale_query)
    locale = result.scalar_one_or_none()
    if not locale:
        raise NotFoundError(f"Locale '{locale_code}' not found.")

    return value.strftime(locale.date_format)


async def format_number(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a number according to locale settings (thousands separator, decimal)."""
    locale_query = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(locale_query)
    locale = result.scalar_one_or_none()
    if not locale:
        raise NotFoundError(f"Locale '{locale_code}' not found.")

    fmt = locale.number_format
    if fmt == "#,###.##":
        return f"{value:,.2f}"
    elif fmt == "#,###":
        return f"{int(value):,}"

    return str(value)


async def format_currency(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a currency value according to locale settings (symbol, decimals)."""
    locale_query = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(locale_query)
    locale = result.scalar_one_or_none()
    if not locale:
        raise NotFoundError(f"Locale '{locale_code}' not found.")

    if locale.currency_code == "JPY":
        return f"¥{int(value):,}"
    elif locale.currency_code == "USD":
        return f"${value:,.2f}"

    return f"{locale.currency_code} {value}"


async def export_translations(db: AsyncSession, locale_code: str, module: str | None = None) -> LocalizationExport:
    """Export translations as JSON-serializable dict."""
    translations = await get_translations_by_module(db, locale_code, module) if module else {}
    if not module:
        all_trans = await get_translations(db, locale_code)
        translations = {t.key: t.value for t in all_trans}

    return LocalizationExport(locale_code=locale_code, translations=translations)


async def import_translations(db: AsyncSession, locale_code: str, data: dict[str, str], module: str) -> int:
    """Import translations from a key-value dict. Upserts existing entries.
    Returns count of imported/updated translations.
    """
    locale_query = select(Locale).where(Locale.code == locale_code)
    result = await db.execute(locale_query)
    locale = result.scalar_one_or_none()
    if not locale:
        raise NotFoundError(f"Locale '{locale_code}' not found.")

    count = 0
    for key, value in data.items():
        validate_translation_key(key)
        validate_translation_value(value)

        query = select(Translation).where(
            Translation.locale_id == locale.id,
            Translation.module == module,
            Translation.key == key
        )
        result = await db.execute(query)
        translation = result.scalar_one_or_none()

        if translation:
            translation.value = value
        else:
            new_trans = Translation(locale_id=locale.id, module=module, key=key, value=value)
            db.add(new_trans)

        count += 1

    await db.commit()
    return count


async def seed_default_locales(db: AsyncSession) -> None:
    """Seed default ja-JP and en-US locales."""
    defaults = [
        {
            "code": "ja-JP", "name": "日本語", "language": "ja", "country": "JP",
            "date_format": "%Y年%m月%d日", "number_format": "#,###", "currency_code": "JPY"
        },
        {
            "code": "en-US", "name": "English", "language": "en", "country": "US",
            "date_format": "%m/%d/%Y", "number_format": "#,###.##", "currency_code": "USD"
        }
    ]

    for d in defaults:
        query = select(Locale).where(Locale.code == d["code"])
        result = await db.execute(query)
        if not result.scalar_one_or_none():
            db.add(Locale(**d))

    await db.commit()

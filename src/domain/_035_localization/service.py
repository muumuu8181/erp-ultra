from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import NotFoundError
from src.domain._035_localization.models import Locale, Translation
from src.domain._035_localization.schemas import (
    LocaleCreate,
    TranslationCreate,
    LocalizationExport,
)
from src.domain._035_localization.validators import (
    validate_locale_create,
    validate_translation_create,
)


async def create_locale(db: AsyncSession, data: LocaleCreate) -> Locale:
    """Create a new locale. Validates code format (xx-XX)."""
    await validate_locale_create(db, data)
    locale = Locale(**data.model_dump())
    db.add(locale)
    await db.commit()
    await db.refresh(locale)
    return locale


async def list_locales(db: AsyncSession, is_active: Optional[bool] = None) -> list[Locale]:
    """List all locales, optionally filtered by active status."""
    query = select(Locale)
    if is_active is not None:
        query = query.filter(Locale.is_active == is_active)
    result = await db.execute(query)
    return list(result.scalars().all())


async def add_translation(db: AsyncSession, data: TranslationCreate) -> Translation:
    """Add a translation entry. Validates key format and value not empty."""
    await validate_translation_create(db, data)
    translation = Translation(**data.model_dump())
    db.add(translation)
    await db.commit()
    await db.refresh(translation)
    return translation


async def get_translations(db: AsyncSession, locale_code: str, module: Optional[str] = None) -> list[Translation]:
    """Get translations for a locale, optionally filtered by module."""
    locale = await _get_locale_by_code(db, locale_code)
    query = select(Translation).filter(Translation.locale_id == locale.id)
    if module:
        query = query.filter(Translation.module == module)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_translations_by_module(db: AsyncSession, locale_code: str, module: str) -> dict[str, str]:
    """Get translations as a key-value dict for a specific locale and module."""
    translations = await get_translations(db, locale_code, module)
    return {t.key: t.value for t in translations}


async def translate(db: AsyncSession, locale_code: str, key: str, default: Optional[str] = None) -> str:
    """Look up a single translation by key. Returns default or key if not found."""
    try:
        locale = await _get_locale_by_code(db, locale_code)
    except NotFoundError:
        return default if default is not None else key

    result = await db.execute(
        select(Translation).filter(
            Translation.locale_id == locale.id,
            Translation.key == key
        )
    )
    translation = result.scalars().first()
    if translation:
        return str(translation.value)
    return default if default is not None else key


async def format_date(db: AsyncSession, locale_code: str, value: date) -> str:
    """Format a date according to locale settings."""
    locale = await _get_locale_by_code(db, locale_code)
    return value.strftime(locale.date_format)


async def format_number(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a number according to locale settings (thousands separator, decimal)."""
    locale = await _get_locale_by_code(db, locale_code)

    fmt = locale.number_format
    if fmt == "#,###":
        return f"{int(value):,}"
    elif fmt == "#,###.##":
        # Format with commas and up to 2 decimal places, removing trailing zeros after decimal
        formatted = f"{value:,.2f}"
        if formatted.endswith(".00"):
            return formatted[:-3]
        if formatted[-1] == "0" and "." in formatted:
            return formatted[:-1]
        return formatted

    # Fallback to simple formatting
    return f"{value}"


async def format_currency(db: AsyncSession, locale_code: str, value: float) -> str:
    """Format a currency value according to locale settings (symbol, decimals)."""
    locale = await _get_locale_by_code(db, locale_code)

    # Basic logic for specific currencies
    if locale.currency_code == "JPY":
        return f"¥{int(value):,}"
    elif locale.currency_code == "USD":
        return f"${value:,.2f}"

    # Generic format using number formatter
    num_str = await format_number(db, locale_code, value)
    return f"{num_str} {locale.currency_code}"


async def export_translations(db: AsyncSession, locale_code: str, module: Optional[str] = None) -> LocalizationExport:
    """Export translations as JSON-serializable dict."""
    translations_list = await get_translations(db, locale_code, module)
    translations_dict = {t.key: t.value for t in translations_list}
    return LocalizationExport(locale_code=locale_code, translations=translations_dict)


async def import_translations(db: AsyncSession, locale_code: str, data: dict[str, str], module: str) -> int:
    """Import translations from a key-value dict. Upserts existing entries.
    Returns count of imported/updated translations.
    """
    locale = await _get_locale_by_code(db, locale_code)

    count = 0
    for key, value in data.items():
        # Validate key
        from src.domain._035_localization.validators import KEY_PATTERN
        if not KEY_PATTERN.match(key):
            continue # skip invalid keys

        result = await db.execute(
            select(Translation).filter(
                Translation.locale_id == locale.id,
                Translation.module == module,
                Translation.key == key
            )
        )
        existing = result.scalars().first()

        if existing:
            existing.value = value
        else:
            new_trans = Translation(
                locale_id=locale.id,
                module=module,
                key=key,
                value=value
            )
            db.add(new_trans)
        count += 1

    await db.commit()
    return count


async def _get_locale_by_code(db: AsyncSession, code: str) -> Locale:
    result = await db.execute(select(Locale).filter(Locale.code == code))
    locale = result.scalars().first()
    if not locale:
        raise NotFoundError(f"Locale with code {code} not found.")
    return locale


async def seed_default_locales(db: AsyncSession) -> None:
    """Seed default locales if they don't exist."""
    locales_to_seed = [
        LocaleCreate(
            code="ja-JP",
            name="日本語",
            language="ja",
            country="JP",
            date_format="%Y年%m月%d日",
            number_format="#,###",
            currency_code="JPY",
            is_active=True
        ),
        LocaleCreate(
            code="en-US",
            name="English",
            language="en",
            country="US",
            date_format="%m/%d/%Y",
            number_format="#,###.##",
            currency_code="USD",
            is_active=True
        )
    ]

    for data in locales_to_seed:
        result = await db.execute(select(Locale).filter(Locale.code == data.code))
        if not result.scalars().first():
            locale = Locale(**data.model_dump())
            db.add(locale)

    await db.commit()

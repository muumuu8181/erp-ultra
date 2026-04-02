import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import ValidationError, DuplicateError
from src.domain._035_localization.schemas import LocaleCreate, TranslationCreate
from src.domain._035_localization.models import Locale, Translation


LOCALE_CODE_PATTERN = re.compile(r"^[a-z]{2}-[A-Z]{2}$")
KEY_PATTERN = re.compile(r"^[a-z_]+\.[a-z_]+\.[a-z_]+$")
CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


async def validate_locale_create(db: AsyncSession, data: LocaleCreate) -> None:
    if not LOCALE_CODE_PATTERN.match(data.code):
        raise ValidationError(f"Invalid locale code format: {data.code}. Expected format: xx-XX")

    if not CURRENCY_CODE_PATTERN.match(data.currency_code):
        raise ValidationError(f"Invalid currency code format: {data.currency_code}. Expected 3 uppercase letters.")

    result = await db.execute(select(Locale).filter(Locale.code == data.code))
    if result.scalars().first():
        raise DuplicateError(f"Locale with code {data.code} already exists.")


async def validate_translation_create(db: AsyncSession, data: TranslationCreate) -> None:
    if not KEY_PATTERN.match(data.key):
        raise ValidationError(f"Invalid key format: {data.key}. Expected format: module.section.key")

    if not data.value or not data.value.strip():
        raise ValidationError("Translation value cannot be empty.")

    result = await db.execute(
        select(Translation).filter(
            Translation.locale_id == data.locale_id,
            Translation.module == data.module,
            Translation.key == data.key
        )
    )
    if result.scalars().first():
        raise DuplicateError(f"Translation with key {data.key} for module {data.module} already exists for this locale.")

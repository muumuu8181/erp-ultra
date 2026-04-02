from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.foundation._001_database.engine import get_db
from src.domain._035_localization.schemas import (
    LocaleCreate,
    LocaleResponse,
    TranslationCreate,
    TranslationResponse,
    TranslationLookup,
    LocalizationExport,
    FormatDateRequest,
    FormatNumberRequest,
    FormatCurrencyRequest,
    ExportTranslationsRequest,
    ImportTranslationsRequest
)
from src.domain._035_localization import service

router = APIRouter(prefix="/api/v1/localization", tags=["localization"])


@router.post("/locales", response_model=LocaleResponse, status_code=status.HTTP_201_CREATED)
async def create_locale(data: LocaleCreate, db: AsyncSession = Depends(get_db)):
    """Create a locale."""
    return await service.create_locale(db, data)


@router.get("/locales", response_model=list[LocaleResponse])
async def list_locales(is_active: Optional[bool] = None, db: AsyncSession = Depends(get_db)):
    """List locales."""
    return await service.list_locales(db, is_active)


@router.post("/translations", response_model=TranslationResponse, status_code=status.HTTP_201_CREATED)
async def add_translation(data: TranslationCreate, db: AsyncSession = Depends(get_db)):
    """Add a translation."""
    return await service.add_translation(db, data)


@router.get("/translations", response_model=list[TranslationResponse])
async def get_translations(
    locale: str = Query(..., alias="locale"),
    module: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get translations for a locale."""
    return await service.get_translations(db, locale, module)


@router.post("/translations/lookup")
async def lookup_translation(data: TranslationLookup, db: AsyncSession = Depends(get_db)) -> str:
    """Look up a translation."""
    return await service.translate(db, data.locale_code, data.key, data.default)


@router.post("/format-date")
async def format_date(data: FormatDateRequest, db: AsyncSession = Depends(get_db)) -> str:
    """Format a date."""
    return await service.format_date(db, data.locale_code, data.value)


@router.post("/format-number")
async def format_number(data: FormatNumberRequest, db: AsyncSession = Depends(get_db)) -> str:
    """Format a number."""
    return await service.format_number(db, data.locale_code, data.value)


@router.post("/format-currency")
async def format_currency(data: FormatCurrencyRequest, db: AsyncSession = Depends(get_db)) -> str:
    """Format a currency value."""
    return await service.format_currency(db, data.locale_code, data.value)


@router.post("/translations/export", response_model=LocalizationExport)
async def export_translations(data: ExportTranslationsRequest, db: AsyncSession = Depends(get_db)):
    """Export translations."""
    return await service.export_translations(db, data.locale_code, data.module)


@router.post("/translations/import")
async def import_translations(data: ImportTranslationsRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Import translations."""
    count = await service.import_translations(db, data.locale_code, data.translations, data.module)
    return {"imported": count}

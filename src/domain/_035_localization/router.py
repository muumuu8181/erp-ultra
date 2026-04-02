from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from src.domain._035_localization import service
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
    ImportTranslationsRequest,
    ImportTranslationsResponse
)


router = APIRouter(prefix="/api/v1/localization", tags=["localization"])


@router.post("/locales", response_model=LocaleResponse, status_code=status.HTTP_201_CREATED)
async def create_locale(
    data: LocaleCreate,
    db: AsyncSession = Depends(get_db)
) -> LocaleResponse:
    """Create a new locale."""
    return await service.create_locale(db, data)


@router.get("/locales", response_model=List[LocaleResponse])
async def list_locales(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> List[LocaleResponse]:
    """List locales."""
    return await service.list_locales(db, is_active=is_active)


@router.post("/translations", response_model=TranslationResponse, status_code=status.HTTP_201_CREATED)
async def add_translation(
    data: TranslationCreate,
    db: AsyncSession = Depends(get_db)
) -> TranslationResponse:
    """Add a translation entry."""
    return await service.add_translation(db, data)


@router.get("/translations", response_model=List[TranslationResponse])
async def get_translations(
    locale: str = Query(..., description="Locale code"),
    module: Optional[str] = Query(None, description="Module filter"),
    db: AsyncSession = Depends(get_db)
) -> List[TranslationResponse]:
    """Get translations for a locale, optionally filtered by module."""
    return await service.get_translations(db, locale_code=locale, module=module)


@router.post("/translations/lookup")
async def lookup_translation(
    data: TranslationLookup,
    db: AsyncSession = Depends(get_db)
) -> str:
    """Look up a single translation by key."""
    return await service.translate(db, data.locale_code, data.key or "", data.default)


@router.post("/format-date")
async def format_date_endpoint(
    data: FormatDateRequest,
    db: AsyncSession = Depends(get_db)
) -> str:
    """Format a date according to locale settings."""
    try:
        # Try to parse string as date for simplicity in API (YYYY-MM-DD)
        dt = datetime.strptime(data.value, "%Y-%m-%d").date()
    except ValueError:
        return data.value # Fallback if not YYYY-MM-DD
    return await service.format_date(db, data.locale_code, dt)


@router.post("/format-number")
async def format_number_endpoint(
    data: FormatNumberRequest,
    db: AsyncSession = Depends(get_db)
) -> str:
    """Format a number according to locale settings."""
    return await service.format_number(db, data.locale_code, data.value)


@router.post("/format-currency")
async def format_currency_endpoint(
    data: FormatCurrencyRequest,
    db: AsyncSession = Depends(get_db)
) -> str:
    """Format a currency value according to locale settings."""
    return await service.format_currency(db, data.locale_code, data.value)


@router.post("/translations/export", response_model=LocalizationExport)
async def export_translations_endpoint(
    locale_code: str = Query(..., description="Locale code"),
    module: Optional[str] = Query(None, description="Module filter"),
    db: AsyncSession = Depends(get_db)
) -> LocalizationExport:
    """Export translations as JSON."""
    return await service.export_translations(db, locale_code, module)


@router.post("/translations/import", response_model=ImportTranslationsResponse)
async def import_translations_endpoint(
    data: ImportTranslationsRequest,
    db: AsyncSession = Depends(get_db)
) -> ImportTranslationsResponse:
    """Import translations from JSON."""
    count = await service.import_translations(db, data.locale_code, data.translations, data.module)
    return ImportTranslationsResponse(imported_count=count)

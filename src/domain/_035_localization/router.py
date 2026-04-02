from datetime import date
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from src.domain._035_localization.schemas import (
    LocaleCreate,
    LocaleResponse,
    TranslationCreate,
    TranslationResponse,
    TranslationLookup,
    LocalizationExport,
)
from src.domain._035_localization.service import (
    create_locale,
    list_locales,
    add_translation,
    get_translations,
    translate,
    format_date,
    format_number,
    format_currency,
    export_translations,
    import_translations,
)

router = APIRouter(prefix="/api/v1/localization", tags=["localization"])


class FormatDateRequest(BaseModel):
    locale_code: str
    value: date


class FormatNumberRequest(BaseModel):
    locale_code: str
    value: float


class FormatCurrencyRequest(BaseModel):
    locale_code: str
    value: float


class ExportRequest(BaseModel):
    locale_code: str
    module: Optional[str] = None


class ImportRequest(BaseModel):
    locale_code: str
    module: str
    translations: Dict[str, str]


@router.post("/locales", response_model=LocaleResponse, status_code=status.HTTP_201_CREATED)
async def api_create_locale(data: LocaleCreate, db: AsyncSession = Depends(get_db)):
    """Create a locale"""
    return await create_locale(db, data)


@router.get("/locales", response_model=List[LocaleResponse], status_code=status.HTTP_200_OK)
async def api_list_locales(is_active: Optional[bool] = None, db: AsyncSession = Depends(get_db)):
    """List locales"""
    return await list_locales(db, is_active)


@router.post("/translations", response_model=TranslationResponse, status_code=status.HTTP_201_CREATED)
async def api_add_translation(data: TranslationCreate, db: AsyncSession = Depends(get_db)):
    """Add a translation"""
    return await add_translation(db, data)


@router.get("/translations", response_model=List[TranslationResponse], status_code=status.HTTP_200_OK)
async def api_get_translations(
    locale: str = Query(..., alias="locale"),
    module: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get translations"""
    return await get_translations(db, locale, module)


@router.post("/translations/lookup", response_model=str, status_code=status.HTTP_200_OK)
async def api_translate(data: TranslationLookup, db: AsyncSession = Depends(get_db)):
    """Look up a translation"""
    # Key should be provided for lookup as per note body: { "locale_code": "ja-JP", "key": "invoice.title", "default": "Invoice" }
    return await translate(db, data.locale_code, data.key, data.default)


@router.post("/format-date", response_model=str, status_code=status.HTTP_200_OK)
async def api_format_date(data: FormatDateRequest, db: AsyncSession = Depends(get_db)):
    """Format a date"""
    return await format_date(db, data.locale_code, data.value)


@router.post("/format-number", response_model=str, status_code=status.HTTP_200_OK)
async def api_format_number(data: FormatNumberRequest, db: AsyncSession = Depends(get_db)):
    """Format a number"""
    return await format_number(db, data.locale_code, data.value)


@router.post("/format-currency", response_model=str, status_code=status.HTTP_200_OK)
async def api_format_currency(data: FormatCurrencyRequest, db: AsyncSession = Depends(get_db)):
    """Format a currency value"""
    return await format_currency(db, data.locale_code, data.value)


@router.post("/translations/export", response_model=LocalizationExport, status_code=status.HTTP_200_OK)
async def api_export_translations(data: ExportRequest, db: AsyncSession = Depends(get_db)):
    """Export translations"""
    return await export_translations(db, data.locale_code, data.module)


@router.post("/translations/import", response_model=int, status_code=status.HTTP_200_OK)
async def api_import_translations(data: ImportRequest, db: AsyncSession = Depends(get_db)):
    """Import translations"""
    return await import_translations(db, data.locale_code, data.translations, data.module)

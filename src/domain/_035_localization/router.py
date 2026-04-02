from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, NotFoundError, ValidationError
from src.domain._035_localization import service
from src.domain._035_localization.schemas import (
    CurrencyFormatRequest,
    DateFormatRequest,
    LocaleCreate,
    LocaleResponse,
    LocalizationExport,
    LocalizationExportRequest,
    LocalizationImportRequest,
    NumberFormatRequest,
    TranslationCreate,
    TranslationLookup,
    TranslationResponse,
)
from src.foundation._001_database.engine import get_db

router = APIRouter(prefix="/api/v1/localization", tags=["localization"])


@router.post("/locales", response_model=LocaleResponse, status_code=201)
async def create_locale(data: LocaleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new locale."""
    try:
        return await service.create_locale(db, data)
    except (ValidationError, DuplicateError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/locales", response_model=list[LocaleResponse])
async def list_locales(is_active: bool | None = None, db: AsyncSession = Depends(get_db)):
    """List locales."""
    return await service.list_locales(db, is_active)


@router.post("/translations", response_model=TranslationResponse, status_code=201)
async def add_translation(data: TranslationCreate, db: AsyncSession = Depends(get_db)):
    """Add a new translation."""
    try:
        return await service.add_translation(db, data)
    except (ValidationError, DuplicateError, NotFoundError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/translations", response_model=list[TranslationResponse])
async def get_translations(
    locale: str = Query(..., description="Locale code"),
    module: str | None = Query(None, description="Module filter"),
    db: AsyncSession = Depends(get_db),
):
    """Get translations, optionally filtered by module."""
    try:
        return await service.get_translations(db, locale, module)
    except NotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/translations/lookup")
async def lookup_translation(data: TranslationLookup, db: AsyncSession = Depends(get_db)):
    """Look up a translation."""
    val = await service.translate(db, data.locale_code, data.key, data.default)
    return {"value": val}


@router.post("/localization/format-date")
async def format_date(data: DateFormatRequest, db: AsyncSession = Depends(get_db)):
    """Format a date."""
    try:
        # we accept str or date in schema, parse it if it's str
        d = date.fromisoformat(data.value) if isinstance(data.value, str) else data.value
        formatted = await service.format_date(db, data.locale_code, d)
        return {"value": formatted}
    except (NotFoundError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/localization/format-number")
async def format_number(data: NumberFormatRequest, db: AsyncSession = Depends(get_db)):
    """Format a number."""
    try:
        formatted = await service.format_number(db, data.locale_code, data.value)
        return {"value": formatted}
    except NotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/localization/format-currency")
async def format_currency(data: CurrencyFormatRequest, db: AsyncSession = Depends(get_db)):
    """Format a currency value."""
    try:
        formatted = await service.format_currency(db, data.locale_code, data.value)
        return {"value": formatted}
    except NotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/translations/export", response_model=LocalizationExport)
async def export_translations(data: LocalizationExportRequest, db: AsyncSession = Depends(get_db)):
    """Export translations as JSON."""
    try:
        return await service.export_translations(db, data.locale_code, data.module)
    except NotFoundError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/translations/import")
async def import_translations(data: LocalizationImportRequest, db: AsyncSession = Depends(get_db)):
    """Import translations from JSON."""
    try:
        count = await service.import_translations(db, data.locale_code, data.translations, data.module)
        return {"imported_count": count}
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=str(e))

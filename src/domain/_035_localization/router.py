"""
Router for the Localization / i18n module.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.foundation._001_database.engine import get_db
from src.domain._035_localization.models import Locale
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
    TranslationExportRequest,
    TranslationImportRequest,
)
from src.domain._035_localization import service
from shared.errors import ValidationError, DuplicateError, NotFoundError


router = APIRouter(prefix="/api/v1/localization", tags=["Localization"])


async def seed_locales(db: AsyncSession) -> None:
    """Pre-seed ja-JP and en-US locales if they don't exist."""
    locales_to_seed = [
        LocaleCreate(
            code="ja-JP", name="日本語", language="ja", country="JP",
            date_format="%Y年%m月%d日", number_format="#,###", currency_code="JPY"
        ),
        LocaleCreate(
            code="en-US", name="English", language="en", country="US",
            date_format="%m/%d/%Y", number_format="#,###.##", currency_code="USD"
        )
    ]

    for loc_data in locales_to_seed:
        result = await db.execute(select(Locale).filter(Locale.code == loc_data.code))
        if not result.scalars().first():
            try:
                await service.create_locale(db, loc_data)
            except (ValidationError, DuplicateError):
                pass


@router.post("/locales", response_model=LocaleResponse, status_code=201)
async def create_locale_endpoint(data: LocaleCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.create_locale(db, data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DuplicateError as e:
        raise HTTPException(status_code=422, detail=e.message)


@router.get("/locales", response_model=List[LocaleResponse])
async def list_locales_endpoint(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    await seed_locales(db) # Ensure seed data exists
    return await service.list_locales(db, is_active)


@router.post("/translations", response_model=TranslationResponse, status_code=201)
async def add_translation_endpoint(data: TranslationCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.add_translation(db, data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DuplicateError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/translations", response_model=List[TranslationResponse])
async def get_translations_endpoint(locale: str = Query(...), module: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    try:
        return await service.get_translations(db, locale_code=locale, module=module)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/translations/lookup")
async def lookup_translation_endpoint(data: TranslationLookup, db: AsyncSession = Depends(get_db)):
    # Note: the issue mentions POST body matching this data
    if not data.key:
        raise HTTPException(status_code=422, detail="Key is required for lookup")
    value = await service.translate(db, data.locale_code, data.key, data.default)
    return {"value": value}


@router.post("/format-date")
async def format_date_endpoint(data: FormatDateRequest, db: AsyncSession = Depends(get_db)):
    await seed_locales(db)
    try:
        formatted = await service.format_date(db, data.locale_code, data.value)
        return {"formatted": formatted}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/format-number")
async def format_number_endpoint(data: FormatNumberRequest, db: AsyncSession = Depends(get_db)):
    await seed_locales(db)
    try:
        formatted = await service.format_number(db, data.locale_code, data.value)
        return {"formatted": formatted}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/format-currency")
async def format_currency_endpoint(data: FormatCurrencyRequest, db: AsyncSession = Depends(get_db)):
    await seed_locales(db)
    try:
        formatted = await service.format_currency(db, data.locale_code, data.value)
        return {"formatted": formatted}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/translations/export", response_model=LocalizationExport)
async def export_translations_endpoint(data: TranslationExportRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await service.export_translations(db, data.locale_code, data.module)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/translations/import")
async def import_translations_endpoint(data: TranslationImportRequest, db: AsyncSession = Depends(get_db)):
    try:
        count = await service.import_translations(db, data.locale_code, data.translations, data.module)
        return {"imported_count": count}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)

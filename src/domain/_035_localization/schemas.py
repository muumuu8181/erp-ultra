from datetime import datetime, date
from typing import Optional
from pydantic import Field

from shared.types import BaseSchema


class LocaleCreate(BaseSchema):
    code: str = Field(..., max_length=5)
    name: str = Field(..., max_length=100)
    language: str = Field(..., max_length=10)
    country: str = Field(..., max_length=10)
    date_format: str = Field(..., max_length=20)
    number_format: str = Field(..., max_length=20)
    currency_code: str = Field(..., max_length=3)
    is_active: bool = True


class LocaleResponse(LocaleCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class TranslationCreate(BaseSchema):
    locale_id: int
    module: str = Field(..., max_length=50)
    key: str = Field(..., max_length=200)
    value: str


class TranslationResponse(TranslationCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class TranslationLookup(BaseSchema):
    locale_code: str
    key: str
    default: Optional[str] = None


class LocalizationExport(BaseSchema):
    locale_code: str
    translations: dict[str, str]


class FormatDateRequest(BaseSchema):
    locale_code: str
    value: date


class FormatNumberRequest(BaseSchema):
    locale_code: str
    value: float


class FormatCurrencyRequest(BaseSchema):
    locale_code: str
    value: float


class ImportTranslationsRequest(BaseSchema):
    locale_code: str
    module: str
    translations: dict[str, str]


class ExportTranslationsRequest(BaseSchema):
    locale_code: str
    module: Optional[str] = None

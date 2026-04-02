from datetime import datetime

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


class LocaleResponse(BaseSchema):
    id: int
    code: str
    name: str
    language: str
    country: str
    date_format: str
    number_format: str
    currency_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TranslationCreate(BaseSchema):
    locale_id: int
    module: str = Field(..., max_length=50)
    key: str = Field(..., max_length=200)
    value: str


class TranslationResponse(BaseSchema):
    id: int
    locale_id: int
    module: str
    key: str
    value: str
    created_at: datetime
    updated_at: datetime


class TranslationLookup(BaseSchema):
    locale_code: str
    key: str
    default: str | None = None


class DateFormatRequest(BaseSchema):
    locale_code: str
    value: str  # or date


class NumberFormatRequest(BaseSchema):
    locale_code: str
    value: float


class CurrencyFormatRequest(BaseSchema):
    locale_code: str
    value: float


class LocalizationExport(BaseSchema):
    locale_code: str
    translations: dict[str, str]


class LocalizationExportRequest(BaseSchema):
    locale_code: str
    module: str | None = None


class LocalizationImportRequest(BaseSchema):
    locale_code: str
    module: str
    translations: dict[str, str]

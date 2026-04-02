from datetime import datetime
from typing import Dict, Optional
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

    class Config:
        from_attributes = True


class TranslationCreate(BaseSchema):
    locale_id: int
    module: str = Field(..., max_length=50)
    key: str = Field(..., max_length=200)
    value: str


class TranslationResponse(TranslationCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranslationLookup(BaseSchema):
    locale_code: str
    module: Optional[str] = None
    key: Optional[str] = None
    default: Optional[str] = None


class LocalizationExport(BaseSchema):
    locale_code: str
    translations: Dict[str, str]

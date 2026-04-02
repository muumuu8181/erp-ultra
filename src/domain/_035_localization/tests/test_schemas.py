import pytest
from pydantic import ValidationError
from datetime import date

from src.domain._035_localization.schemas import (
    LocaleCreate,
    TranslationCreate,
    FormatDateRequest
)

def test_locale_create_schema():
    # Valid
    data = LocaleCreate(
        code="ja-JP",
        name="日本語",
        language="ja",
        country="JP",
        date_format="%Y年%m月%d日",
        number_format="#,###",
        currency_code="JPY"
    )
    assert data.code == "ja-JP"

    # Invalid - code too long
    with pytest.raises(ValidationError):
        LocaleCreate(
            code="ja-JAPAN",
            name="日本語",
            language="ja",
            country="JP",
            date_format="%Y年%m月%d日",
            number_format="#,###",
            currency_code="JPY"
        )

def test_translation_create_schema():
    data = TranslationCreate(
        locale_id=1,
        module="sales",
        key="sales.order.title",
        value="Sales Order"
    )
    assert data.module == "sales"

    with pytest.raises(ValidationError):
        TranslationCreate(
            locale_id=1,
            module="a" * 51,
            key="sales.order.title",
            value="Sales Order"
        )

def test_format_date_request():
    data = FormatDateRequest(
        locale_code="en-US",
        value=date(2025, 1, 15)
    )
    assert data.locale_code == "en-US"
    assert data.value == date(2025, 1, 15)

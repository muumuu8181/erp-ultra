import pytest

from shared.errors import ValidationError
from src.domain._035_localization.validators import (
    validate_currency_code,
    validate_locale_code,
    validate_translation_key,
    validate_translation_value,
)


def test_validate_locale_code():
    validate_locale_code("ja-JP")
    validate_locale_code("en-US")
    with pytest.raises(ValidationError):
        validate_locale_code("japanese")
    with pytest.raises(ValidationError):
        validate_locale_code("JA-jp")
    with pytest.raises(ValidationError):
        validate_locale_code("jJP")


def test_validate_translation_key():
    validate_translation_key("invoice.title.main")
    validate_translation_key("sales_order.header.total_amount")
    with pytest.raises(ValidationError):
        validate_translation_key("Invoice")
    with pytest.raises(ValidationError):
        validate_translation_key("invoice.title")
    with pytest.raises(ValidationError):
        validate_translation_key("INV.TITLE.MAIN")


def test_validate_translation_value():
    validate_translation_value("Hello")
    with pytest.raises(ValidationError):
        validate_translation_value("")
    with pytest.raises(ValidationError):
        validate_translation_value("   ")


def test_validate_currency_code():
    validate_currency_code("USD")
    validate_currency_code("JPY")
    with pytest.raises(ValidationError):
        validate_currency_code("usd")
    with pytest.raises(ValidationError):
        validate_currency_code("US")
    with pytest.raises(ValidationError):
        validate_currency_code("USDD")

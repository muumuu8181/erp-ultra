import pytest
from shared.errors import ValidationError
from src.domain._035_localization.validators import (
    validate_locale_code,
    validate_translation_key,
    validate_translation_value,
    validate_currency_code
)

def test_validate_locale_code():
    # Pass
    validate_locale_code("ja-JP")
    validate_locale_code("en-US")
    validate_locale_code("fr-FR")

    # Fail
    with pytest.raises(ValidationError):
        validate_locale_code("japanese")
    with pytest.raises(ValidationError):
        validate_locale_code("JA-jp")
    with pytest.raises(ValidationError):
        validate_locale_code("jJP")
    with pytest.raises(ValidationError):
        validate_locale_code("en_US")


def test_validate_translation_key():
    # Pass
    validate_translation_key("invoice.title.main")
    validate_translation_key("sales_order.header.status")

    # Fail
    with pytest.raises(ValidationError):
        validate_translation_key("Invoice")
    with pytest.raises(ValidationError):
        validate_translation_key("invoice.title")
    with pytest.raises(ValidationError):
        validate_translation_key("INV.TITLE.MAIN")
    with pytest.raises(ValidationError):
        validate_translation_key("invoice-title-main")


def test_validate_translation_value():
    # Pass
    validate_translation_value("Hello")
    validate_translation_value("こんにちは")

    # Fail
    with pytest.raises(ValidationError):
        validate_translation_value("")
    with pytest.raises(ValidationError):
        validate_translation_value("   ")


def test_validate_currency_code():
    # Pass
    validate_currency_code("JPY")
    validate_currency_code("USD")
    validate_currency_code("EUR")

    # Fail
    with pytest.raises(ValidationError):
        validate_currency_code("JP")
    with pytest.raises(ValidationError):
        validate_currency_code("jpy")
    with pytest.raises(ValidationError):
        validate_currency_code("YEN1")
    with pytest.raises(ValidationError):
        validate_currency_code("123")

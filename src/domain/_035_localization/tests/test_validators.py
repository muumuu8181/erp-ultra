"""
Tests for localization validators.
"""
import pytest
from shared.errors import ValidationError

from src.domain._035_localization.validators import (
    validate_locale_code_format,
    validate_key_format,
    validate_value_not_empty,
    validate_currency_code
)


def test_validate_locale_code_format():
    # Pass cases
    validate_locale_code_format("ja-JP")
    validate_locale_code_format("en-US")
    validate_locale_code_format("fr-FR")

    # Fail cases
    with pytest.raises(ValidationError):
        validate_locale_code_format("japanese")

    with pytest.raises(ValidationError):
        validate_locale_code_format("JA-jp")

    with pytest.raises(ValidationError):
        validate_locale_code_format("jJP")


def test_validate_key_format():
    # Pass cases
    validate_key_format("invoice.title.main")
    validate_key_format("core.auth.login_failed")

    # Fail cases
    with pytest.raises(ValidationError):
        validate_key_format("Invoice")

    with pytest.raises(ValidationError):
        validate_key_format("invoice.title")

    with pytest.raises(ValidationError):
        validate_key_format("INV.TITLE.MAIN")


def test_validate_value_not_empty():
    # Pass cases
    validate_value_not_empty("Valid translation")
    validate_value_not_empty("   Valid   ")

    # Fail cases
    with pytest.raises(ValidationError):
        validate_value_not_empty("")

    with pytest.raises(ValidationError):
        validate_value_not_empty("   ")


def test_validate_currency_code():
    # Pass cases
    validate_currency_code("JPY")
    validate_currency_code("USD")
    validate_currency_code("EUR")

    # Fail cases
    with pytest.raises(ValidationError):
        validate_currency_code("jpy")

    with pytest.raises(ValidationError):
        validate_currency_code("US")

    with pytest.raises(ValidationError):
        validate_currency_code("YEN1")

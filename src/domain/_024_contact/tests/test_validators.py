import pytest
from shared.errors import ValidationError as SharedValidationError
from domain._024_contact.validators import validate_phone_number

def test_validate_phone_number_valid():
    validate_phone_number("+1234567890")
    validate_phone_number("123-456-7890")
    validate_phone_number("(123) 456 7890")
    validate_phone_number(None)  # None is valid/ignored

def test_validate_phone_number_invalid():
    with pytest.raises(SharedValidationError):
        validate_phone_number("invalid-phone")

    with pytest.raises(SharedValidationError):
        validate_phone_number("+++")

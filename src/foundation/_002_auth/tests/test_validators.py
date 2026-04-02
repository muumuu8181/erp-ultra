import pytest
from shared.errors import ValidationError
from src.foundation._002_auth.validators import (
    validate_password_strength,
    validate_email_format,
    validate_username_format
)

def test_validate_password_strength_valid():
    # Should not raise exception
    validate_password_strength("Valid1Password")
    validate_password_strength("AnotherVal!d1")
    validate_password_strength("Sh0rtB1g")

def test_validate_password_strength_too_short():
    with pytest.raises(ValidationError) as exc_info:
        validate_password_strength("Short1A")
    assert exc_info.value.field == "password"

def test_validate_password_strength_no_uppercase():
    with pytest.raises(ValidationError) as exc_info:
        validate_password_strength("nouppercase123")
    assert exc_info.value.field == "password"

def test_validate_password_strength_no_digit():
    with pytest.raises(ValidationError) as exc_info:
        validate_password_strength("NoDigitPassword")
    assert exc_info.value.field == "password"

def test_validate_email_format_valid():
    validate_email_format("test@example.com")
    validate_email_format("user.name+tag@domain.co.uk")

def test_validate_email_format_invalid():
    invalid_emails = [
        "plainaddress",
        "@missingusername.com",
        "username@.com",
        "username@domain"
    ]
    for email in invalid_emails:
        with pytest.raises(ValidationError) as exc_info:
            validate_email_format(email)
        assert exc_info.value.field == "email"

def test_validate_username_format_valid():
    validate_username_format("user_name")
    validate_username_format("user123")
    validate_username_format("USR_abc")

def test_validate_username_format_too_short():
    with pytest.raises(ValidationError) as exc_info:
        validate_username_format("us")
    assert exc_info.value.field == "username"

def test_validate_username_format_invalid_chars():
    with pytest.raises(ValidationError) as exc_info:
        validate_username_format("user-name") # hyphen is invalid
    assert exc_info.value.field == "username"

    with pytest.raises(ValidationError) as exc_info:
        validate_username_format("user name") # space is invalid
    assert exc_info.value.field == "username"

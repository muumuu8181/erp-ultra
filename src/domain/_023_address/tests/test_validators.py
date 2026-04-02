import pytest
from shared.errors import ValidationError
from src.domain._023_address.validators import validate_postal_code, validate_address_create, validate_address_update
from src.domain._023_address.schemas import AddressCreate, AddressUpdate

def test_validate_postal_code_valid() -> None:
    # These should not raise exceptions
    validate_postal_code("123-4567")
    validate_postal_code("1234567")

def test_validate_postal_code_invalid() -> None:
    invalid_codes = [
        "12-4567",
        "123-456",
        "123456",
        "12345678",
        "abc-defg",
        "123-45678"
    ]

    for code in invalid_codes:
        with pytest.raises(ValidationError):
            validate_postal_code(code)

def test_validate_address_create() -> None:
    schema = AddressCreate(
        postal_code="123-4567",
        prefecture="Tokyo",
        city="Minato-ku",
        street="1-2-3"
    )
    validate_address_create(schema)  # Should not raise

    invalid_schema = AddressCreate(
        postal_code="invalid",
        prefecture="Tokyo",
        city="Minato-ku",
        street="1-2-3"
    )
    with pytest.raises(ValidationError):
        validate_address_create(invalid_schema)

def test_validate_address_update() -> None:
    schema = AddressUpdate(postal_code="123-4567")
    validate_address_update(schema)  # Should not raise

    empty_schema = AddressUpdate()
    validate_address_update(empty_schema)  # Should not raise, postal_code is None

    invalid_schema = AddressUpdate(postal_code="invalid")
    with pytest.raises(ValidationError):
        validate_address_update(invalid_schema)

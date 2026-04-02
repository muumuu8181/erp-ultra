import pytest
from pydantic import ValidationError
from domain._024_contact.schemas import ContactCreate, ContactUpdate

def test_contact_create_schema_valid():
    data = {"first_name": "John", "last_name": "Doe", "email": "john@example.com"}
    schema = ContactCreate(**data)
    assert schema.first_name == "John"
    assert schema.email == "john@example.com"

def test_contact_create_schema_invalid_email():
    data = {"first_name": "John", "last_name": "Doe", "email": "not-an-email"}
    with pytest.raises(ValidationError):
        ContactCreate(**data)

def test_contact_update_schema():
    data = {"first_name": "Jane"}
    schema = ContactUpdate(**data)
    assert schema.first_name == "Jane"
    assert schema.last_name is None

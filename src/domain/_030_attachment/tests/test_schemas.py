import pytest
from pydantic import ValidationError
from src.domain._030_attachment.schemas import AttachmentCreate, AttachmentResponse

def test_attachment_create_schema_valid():
    data = {"code": "ATT-123", "name": "document.pdf"}
    schema = AttachmentCreate(**data)
    assert schema.code == "ATT-123"
    assert schema.name == "document.pdf"

def test_attachment_create_schema_invalid():
    with pytest.raises(ValidationError):
        AttachmentCreate(code="ATT-123")  # Missing name

def test_attachment_create_schema_invalid_empty_fields():
    with pytest.raises(ValidationError):
        AttachmentCreate(code="", name="document.pdf")
    with pytest.raises(ValidationError):
        AttachmentCreate(code="ATT-123", name="  ")

def test_attachment_response_schema():
    data = {"id": 1, "code": "ATT-123", "name": "document.pdf"}
    schema = AttachmentResponse(**data)
    assert schema.id == 1
    assert schema.code == "ATT-123"

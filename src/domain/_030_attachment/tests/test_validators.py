from src.domain._030_attachment.validators import validate_attachment_name, validate_attachment_code

def test_validate_attachment_name_valid():
    assert validate_attachment_name("file.txt") is True

def test_validate_attachment_name_invalid():
    assert validate_attachment_name("") is False
    assert validate_attachment_name("   ") is False

def test_validate_attachment_code_valid():
    assert validate_attachment_code("ATT-01") is True

def test_validate_attachment_code_invalid():
    assert validate_attachment_code("") is False
    assert validate_attachment_code("   ") is False

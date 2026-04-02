import pytest
from shared.errors import ValidationError
from src.foundation._004_api_gateway.validators import validate_path, validate_target_url


def test_validate_path_valid():
    validate_path("/api/v1/test")


def test_validate_path_invalid():
    with pytest.raises(ValidationError) as exc_info:
        validate_path("api/v1/test")
    assert exc_info.value.field == "path"
    assert "start with '/'" in exc_info.value.message


def test_validate_target_url_valid():
    validate_target_url("http://localhost:8080")
    validate_target_url("https://example.com/api")


def test_validate_target_url_invalid_format():
    with pytest.raises(ValidationError) as exc_info:
        validate_target_url("not-a-url")
    assert exc_info.value.field == "target_url"


def test_validate_target_url_invalid_scheme():
    with pytest.raises(ValidationError) as exc_info:
        validate_target_url("ftp://example.com")
    assert exc_info.value.field == "target_url"
    assert "scheme must be http or https" in exc_info.value.message

import pytest
from shared.errors import ValidationError
from src.inventory._065_inventory_api.validators import validate_http_method, validate_endpoint_path

def test_validate_http_method_valid():
    validate_http_method("GET")
    validate_http_method("post")

def test_validate_http_method_invalid():
    with pytest.raises(ValidationError):
        validate_http_method("INVALID")

def test_validate_endpoint_path_valid():
    validate_endpoint_path("/valid/path")

def test_validate_endpoint_path_invalid():
    with pytest.raises(ValidationError):
        validate_endpoint_path("invalid/path")

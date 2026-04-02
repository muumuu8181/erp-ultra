import pytest
from shared.errors import ValidationError
from src.foundation._008_cache.validators import (
    validate_cache_key, validate_cache_value, validate_ttl, validate_module_name
)

def test_validate_cache_key_valid():
    validate_cache_key("inventory:products:123")
    validate_cache_key("orders:customer:456")
    validate_cache_key("cache:stats")

def test_validate_cache_key_single_segment():
    with pytest.raises(ValidationError):
        validate_cache_key("inventory")

def test_validate_cache_key_uppercase():
    with pytest.raises(ValidationError):
        validate_cache_key("Inventory:Products")

def test_validate_cache_key_too_long():
    with pytest.raises(ValidationError):
        validate_cache_key("a" * 25 + ":" + "b" * 26)

def test_validate_cache_key_too_many_segments():
    with pytest.raises(ValidationError):
        validate_cache_key("a:b:c:d:e:f")

def test_validate_cache_value_valid():
    validate_cache_value('{"id": 1}')
    validate_cache_value('123')
    validate_cache_value('"string"')

def test_validate_cache_value_invalid():
    with pytest.raises(ValidationError):
        validate_cache_value('{invalid json}')

def test_validate_ttl_valid():
    validate_ttl(1)
    validate_ttl(60)
    validate_ttl(86400)

def test_validate_ttl_zero():
    with pytest.raises(ValidationError):
        validate_ttl(0)

def test_validate_ttl_too_large():
    with pytest.raises(ValidationError):
        validate_ttl(86401)

def test_validate_module_name_valid():
    validate_module_name("inventory")
    validate_module_name("cache")

def test_validate_module_name_invalid():
    with pytest.raises(ValidationError):
        validate_module_name("unknown_module")

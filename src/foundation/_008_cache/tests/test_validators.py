import pytest
from shared.errors import ValidationError
from src.foundation._008_cache.validators import (
    validate_cache_key,
    validate_cache_value,
    validate_ttl,
    validate_module_name
)

def test_validate_cache_key_valid():
    validate_cache_key("inventory:products:123")
    validate_cache_key("orders:customer:456")
    validate_cache_key("cache:stats")

def test_validate_cache_key_single_segment():
    with pytest.raises(ValidationError) as exc:
        validate_cache_key("inventory")
    assert exc.value.field == "key"

def test_validate_cache_key_uppercase():
    with pytest.raises(ValidationError) as exc:
        validate_cache_key("Inventory:Products")
    assert exc.value.field == "key"

def test_validate_cache_key_too_long():
    long_key = "a" * 20 + ":" + "b" * 20 + ":" + "c" * 20
    with pytest.raises(ValidationError) as exc:
        validate_cache_key(long_key)
    assert exc.value.field == "key"

def test_validate_cache_key_too_many_segments():
    with pytest.raises(ValidationError) as exc:
        validate_cache_key("a:b:c:d:e:f")
    assert exc.value.field == "key"

def test_validate_cache_value_valid():
    validate_cache_value('{"name": "test"}')
    validate_cache_value('[1, 2, 3]')
    validate_cache_value('"string"')

def test_validate_cache_value_invalid():
    with pytest.raises(ValidationError) as exc:
        validate_cache_value("{invalid_json}")
    assert exc.value.field == "value"

def test_validate_ttl_valid():
    validate_ttl(1)
    validate_ttl(60)
    validate_ttl(3600)
    validate_ttl(86400)

def test_validate_ttl_zero():
    with pytest.raises(ValidationError) as exc:
        validate_ttl(0)
    assert exc.value.field == "ttl_seconds"

def test_validate_ttl_too_large():
    with pytest.raises(ValidationError) as exc:
        validate_ttl(86401)
    assert exc.value.field == "ttl_seconds"

def test_validate_module_name_valid():
    validate_module_name("inventory")
    validate_module_name("system")

def test_validate_module_name_invalid():
    with pytest.raises(ValidationError) as exc:
        validate_module_name("unknown")
    assert exc.value.field == "module"

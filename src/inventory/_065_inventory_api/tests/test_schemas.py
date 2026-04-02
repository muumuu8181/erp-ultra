import pytest
from pydantic import ValidationError
from src.inventory._065_inventory_api.schemas import InventoryEndpointCreate

def test_inventory_endpoint_create_schema_valid():
    data = {
        "name": "Test",
        "path": "/test",
        "method": "POST"
    }
    schema = InventoryEndpointCreate(**data)
    assert schema.name == "Test"
    assert schema.path == "/test"
    assert schema.method == "POST"
    assert schema.is_active is True

def test_inventory_endpoint_create_schema_invalid():
    data = {
        "name": "Test",
        "path": "/test"
    }
    with pytest.raises(ValidationError):
        InventoryEndpointCreate(**data)

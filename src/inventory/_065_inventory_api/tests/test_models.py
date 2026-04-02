import pytest
from src.inventory._065_inventory_api.models import InventoryEndpoint

def test_inventory_endpoint_model_init():
    endpoint = InventoryEndpoint(
        name="Test Endpoint",
        path="/api/test",
        method="GET",
        is_active=True
    )
    assert endpoint.name == "Test Endpoint"
    assert endpoint.path == "/api/test"
    assert endpoint.method == "GET"
    assert endpoint.is_active is True

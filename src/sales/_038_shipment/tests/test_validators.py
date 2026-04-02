import pytest
from decimal import Decimal

from src.sales._038_shipment.schemas import ShipmentCreate, ShipmentUpdate, ShipmentItemCreate
from src.sales._038_shipment.validators import validate_shipment_create, validate_shipment_update
from shared.errors import ValidationError

def test_validate_shipment_create_valid():
    data = ShipmentCreate(
        sales_order_id=1,
        customer_id=1,
        status="draft",
        items=[ShipmentItemCreate(product_id=1, quantity=Decimal("10.0"))]
    )
    validate_shipment_create(data)

def test_validate_shipment_create_invalid_status():
    data = ShipmentCreate(
        sales_order_id=1,
        customer_id=1,
        status="shipped",
        items=[ShipmentItemCreate(product_id=1, quantity=Decimal("10.0"))]
    )
    with pytest.raises(ValidationError):
        validate_shipment_create(data)

def test_validate_shipment_create_no_items():
    data = ShipmentCreate(sales_order_id=1, customer_id=1, items=[])
    with pytest.raises(ValidationError):
        validate_shipment_create(data)

def test_validate_shipment_create_zero_quantity():
    data = ShipmentCreate(
        sales_order_id=1,
        customer_id=1,
        items=[ShipmentItemCreate(product_id=1, quantity=Decimal("0.0"))]
    )
    with pytest.raises(ValidationError):
        validate_shipment_create(data)

def test_validate_shipment_update_valid():
    data = ShipmentUpdate(status="shipped")
    validate_shipment_update(data)

def test_validate_shipment_update_invalid():
    data = ShipmentUpdate(status="unknown")
    with pytest.raises(ValidationError):
        validate_shipment_update(data)

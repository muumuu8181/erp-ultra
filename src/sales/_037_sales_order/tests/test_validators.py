import pytest
from decimal import Decimal

from shared.errors import ValidationError
from src.sales._037_sales_order.schemas import SalesOrderCreate, SalesOrderItemCreate
from src.sales._037_sales_order.validators import validate_sales_order_create

def test_validate_sales_order_create_empty_items():
    data = SalesOrderCreate(customer_id=1, items=[])
    with pytest.raises(ValidationError) as exc:
        validate_sales_order_create(data)
    assert exc.value.field == "items"

def test_validate_sales_order_create_invalid_quantity():
    data = SalesOrderCreate(
        customer_id=1,
        items=[SalesOrderItemCreate(product_id=1, quantity=Decimal("-1"), unit_price=Decimal("10.00"))]
    )
    with pytest.raises(ValidationError) as exc:
        validate_sales_order_create(data)
    assert "quantity" in exc.value.field

def test_validate_sales_order_create_negative_price():
    data = SalesOrderCreate(
        customer_id=1,
        items=[SalesOrderItemCreate(product_id=1, quantity=Decimal("1"), unit_price=Decimal("-10.00"))]
    )
    with pytest.raises(ValidationError) as exc:
        validate_sales_order_create(data)
    assert "unit_price" in exc.value.field

import pytest
from decimal import Decimal
from pydantic import ValidationError as PydanticValidationError

from src.sales._037_sales_order.schemas import SalesOrderCreate

def test_sales_order_create_valid():
    data = {
        "customer_id": 1,
        "items": [
            {"product_id": 10, "quantity": "2", "unit_price": "10.50"}
        ]
    }
    schema = SalesOrderCreate(**data)
    assert schema.customer_id == 1
    assert len(schema.items) == 1
    assert schema.items[0].quantity == Decimal("2")
    assert schema.items[0].unit_price == Decimal("10.50")

def test_sales_order_create_invalid_types():
    data = {
        "customer_id": "not-an-int",
        "items": []
    }
    with pytest.raises(PydanticValidationError):
        SalesOrderCreate(**data)

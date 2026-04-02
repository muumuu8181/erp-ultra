"""
Sales Order Validators
"""
from decimal import Decimal
from shared.errors import ValidationError
from src.sales._037_sales_order.schemas import SalesOrderCreate


def validate_sales_order_create(data: SalesOrderCreate) -> None:
    """
    Validate sales order creation payload.

    Ensures:
    - Order has at least one item.
    - Quantity is greater than 0.
    - Unit price is greater than or equal to 0.
    """
    if not data.items:
        raise ValidationError("Sales order must contain at least one item", field="items")

    for index, item in enumerate(data.items):
        if item.quantity <= Decimal("0"):
            raise ValidationError(f"Item quantity must be greater than 0", field=f"items[{index}].quantity")

        if item.unit_price < Decimal("0"):
            raise ValidationError(f"Item unit price cannot be negative", field=f"items[{index}].unit_price")

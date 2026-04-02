from datetime import date
from decimal import Decimal
from shared.errors import ValidationError
from src.sales._044_discount.models import DiscountType

def validate_discount_value(value: Decimal, discount_type: DiscountType) -> None:
    if value <= 0:
        raise ValidationError("Discount value must be greater than 0", "value")
    if discount_type == DiscountType.percentage and value > 100:
        raise ValidationError("Percentage discount cannot exceed 100", "value")

def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise ValidationError("start_date must be less than or equal to end_date", "start_date")

import pytest
from datetime import date
from decimal import Decimal
from src.sales._049_promotion.schemas import PromotionCreate
from src.sales._049_promotion.models import PromotionType

def test_promotion_create_schema():
    data = {
        "code": "TEST1",
        "name": "Test Promo",
        "promotion_type": PromotionType.PERCENTAGE_OFF,
        "value": Decimal("10.5"),
        "product_codes": ["P1"],
        "customer_groups": [],
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 12, 31),
        "is_active": True
    }
    schema = PromotionCreate(**data)
    assert schema.code == "TEST1"
    assert schema.value == Decimal("10.5")

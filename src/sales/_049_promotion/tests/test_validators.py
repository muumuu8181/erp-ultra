import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

from shared.errors import ValidationError, DuplicateError
from src.sales._049_promotion.validators import (
    validate_promotion_create,
    is_promotion_active,
    check_redemption_limit,
    is_customer_eligible
)
from src.sales._049_promotion.models import Promotion, PromotionType
from src.sales._049_promotion.schemas import PromotionCreate

@pytest.mark.asyncio
async def test_validate_promotion_create_valid():
    class MockResult:
        def scalars(self):
            class MockScalars:
                def first(self):
                    return None
            return MockScalars()

    db = AsyncMock()
    db.execute.return_value = MockResult()

    data = PromotionCreate(
        code="VAL-PROMO",
        name="Valid Promo",
        promotion_type=PromotionType.PERCENTAGE_OFF,
        value=Decimal("15.0"),
        product_codes=["P1"],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )

    await validate_promotion_create(db, data)

@pytest.mark.asyncio
async def test_validate_promotion_create_invalid_dates():
    db = AsyncMock()
    data = PromotionCreate(
        code="VAL-PROMO",
        name="Valid Promo",
        promotion_type=PromotionType.PERCENTAGE_OFF,
        value=Decimal("15.0"),
        product_codes=["P1"],
        customer_groups=[],
        start_date=date(2023, 12, 31),
        end_date=date(2023, 1, 1),
        is_active=True
    )

    with pytest.raises(ValidationError, match="start_date must be before or equal to end_date"):
        await validate_promotion_create(db, data)

@pytest.mark.asyncio
async def test_validate_promotion_create_invalid_value():
    db = AsyncMock()
    data = PromotionCreate(
        code="VAL-PROMO",
        name="Valid Promo",
        promotion_type=PromotionType.PERCENTAGE_OFF,
        value=Decimal("0.0"),
        product_codes=["P1"],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )

    with pytest.raises(ValidationError, match="value must be greater than 0"):
        await validate_promotion_create(db, data)

@pytest.mark.asyncio
async def test_validate_promotion_create_empty_products():
    db = AsyncMock()
    data = PromotionCreate(
        code="VAL-PROMO",
        name="Valid Promo",
        promotion_type=PromotionType.PERCENTAGE_OFF,
        value=Decimal("15.0"),
        product_codes=[],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )

    with pytest.raises(ValidationError, match="product_codes must not be empty"):
        await validate_promotion_create(db, data)

@pytest.mark.asyncio
async def test_validate_promotion_create_duplicate_code():
    class MockResult:
        def scalars(self):
            class MockScalars:
                def first(self):
                    return Promotion(id=1)
            return MockScalars()

    db = AsyncMock()
    db.execute.return_value = MockResult()

    data = PromotionCreate(
        code="DUP-PROMO",
        name="Duplicate Promo",
        promotion_type=PromotionType.PERCENTAGE_OFF,
        value=Decimal("15.0"),
        product_codes=["P1"],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )

    with pytest.raises(DuplicateError, match="Promotion with code DUP-PROMO already exists"):
        await validate_promotion_create(db, data)

@pytest.mark.asyncio
async def test_validate_promotion_create_percentage_too_high():
    db = AsyncMock()
    data = PromotionCreate(
        code="VAL-PROMO",
        name="Valid Promo",
        promotion_type=PromotionType.PERCENTAGE_OFF,
        value=Decimal("150.0"),
        product_codes=["P1"],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )

    with pytest.raises(ValidationError, match="Percentage off value cannot be greater than 100"):
        await validate_promotion_create(db, data)

def test_is_promotion_active():
    promo = Promotion(
        start_date=date(2023, 5, 1),
        end_date=date(2023, 5, 31),
        is_active=True
    )

    assert is_promotion_active(promo, date(2023, 5, 15)) is True
    assert is_promotion_active(promo, date(2023, 4, 30)) is False
    assert is_promotion_active(promo, date(2023, 6, 1)) is False

    promo.is_active = False
    assert is_promotion_active(promo, date(2023, 5, 15)) is False

def test_check_redemption_limit():
    promo = Promotion(max_redemptions=None, current_redemptions=100)
    assert check_redemption_limit(promo) is True

    promo = Promotion(max_redemptions=10, current_redemptions=5)
    assert check_redemption_limit(promo) is True

    promo = Promotion(max_redemptions=10, current_redemptions=10)
    assert check_redemption_limit(promo) is False

def test_is_customer_eligible():
    promo = Promotion(customer_groups=[])
    assert is_customer_eligible(promo, None) is True
    assert is_customer_eligible(promo, "VIP") is True

    promo = Promotion(customer_groups=["VIP", "MEMBERS"])
    assert is_customer_eligible(promo, None) is False
    assert is_customer_eligible(promo, "VIP") is True
    assert is_customer_eligible(promo, "GUEST") is False

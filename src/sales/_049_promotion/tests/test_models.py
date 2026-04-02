import pytest
from sqlalchemy.exc import IntegrityError
from datetime import date
from decimal import Decimal

from src.sales._049_promotion.models import Promotion, PromotionRedemption, PromotionType

@pytest.mark.asyncio
async def test_create_promotion(db_session):
    promo = Promotion(
        code="TEST-PROMO",
        name="Test Promotion",
        promotion_type=PromotionType.PERCENTAGE_OFF,
        value=Decimal("10.00"),
        product_codes=["P1", "P2"],
        customer_groups=["G1"],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )
    db_session.add(promo)
    await db_session.commit()
    await db_session.refresh(promo)

    assert promo.id is not None
    assert promo.code == "TEST-PROMO"
    assert promo.current_redemptions == 0

@pytest.mark.asyncio
async def test_promotion_unique_code(db_session):
    promo1 = Promotion(
        code="DUP-PROMO",
        name="Promo 1",
        promotion_type=PromotionType.FIXED_OFF,
        value=Decimal("100.00"),
        product_codes=[],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )
    db_session.add(promo1)
    await db_session.commit()

    promo2 = Promotion(
        code="DUP-PROMO",
        name="Promo 2",
        promotion_type=PromotionType.FIXED_OFF,
        value=Decimal("50.00"),
        product_codes=[],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )
    db_session.add(promo2)
    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_create_promotion_redemption(db_session):
    promo = Promotion(
        code="RED-PROMO",
        name="Redemption Promo",
        promotion_type=PromotionType.FIXED_OFF,
        value=Decimal("50.00"),
        product_codes=[],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )
    db_session.add(promo)
    await db_session.commit()
    await db_session.refresh(promo)

    redemption = PromotionRedemption(
        promotion_id=promo.id,
        order_number="ORD-123",
        customer_code="CUST-1",
        redeemed_value=Decimal("50.00")
    )
    db_session.add(redemption)
    await db_session.commit()
    await db_session.refresh(redemption)

    assert redemption.id is not None
    assert redemption.promotion_id == promo.id

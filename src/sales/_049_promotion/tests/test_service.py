import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from shared.errors import NotFoundError
from src.sales._049_promotion.service import (
    create_promotion,
    update_promotion,
    evaluate_promotions,
    redeem_promotion,
    list_active,
    get_redemptions,
    deactivate
)
from src.sales._049_promotion.models import Promotion, PromotionType
from src.sales._049_promotion.schemas import PromotionCreate, PromotionUpdate, PromotionEvaluateRequest, CartItem

@pytest.fixture
def mock_today():
    class MockDate(date):
        @classmethod
        def today(cls):
            return date(2023, 6, 15)
    return MockDate

@pytest.mark.asyncio
async def test_create_and_update_promotion(db_session):
    data = PromotionCreate(
        code="SERV-PROMO",
        name="Service Promo",
        promotion_type=PromotionType.PERCENTAGE_OFF,
        value=Decimal("20.0"),
        product_codes=["P1", "P2"],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )

    promo = await create_promotion(db_session, data)
    assert promo.id is not None
    assert promo.code == "SERV-PROMO"

    update_data = PromotionUpdate(name="Updated Promo")
    updated_promo = await update_promotion(db_session, promo.id, update_data)
    assert updated_promo.name == "Updated Promo"

@pytest.mark.asyncio
async def test_update_not_found(db_session):
    with pytest.raises(NotFoundError):
        update_data = PromotionUpdate(name="Updated Promo")
        await update_promotion(db_session, 9999, update_data)

@pytest.mark.asyncio
async def test_evaluate_promotions_percentage_off(db_session):
    with patch('src.sales._049_promotion.service.date') as mock_date:
        mock_date.today.return_value = date(2023, 6, 15)

        # Create an active promotion
        promo = Promotion(
            code="EVAL-PERC",
            name="Percentage Off",
            promotion_type=PromotionType.PERCENTAGE_OFF,
            value=Decimal("10.0"), # 10%
            product_codes=["P1"],
            customer_groups=[],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            is_active=True
        )
        db_session.add(promo)
        await db_session.commit()

        request = PromotionEvaluateRequest(
            cart_items=[
                CartItem(product_code="P1", quantity=Decimal("2"), unit_price=Decimal("100.0")),
                CartItem(product_code="P2", quantity=Decimal("1"), unit_price=Decimal("50.0"))
            ],
            customer_code="C1"
        )

        response = await evaluate_promotions(db_session, request)

        assert len(response.applicable_promotions) == 1
        assert response.applicable_promotions[0].discount_value == Decimal("20.0") # 10% of 2*100
        assert response.best_promotion is not None
        assert response.best_promotion.code == "EVAL-PERC"
        assert response.total_savings == Decimal("20.0")

@pytest.mark.asyncio
async def test_evaluate_promotions_fixed_off(db_session):
    with patch('src.sales._049_promotion.service.date') as mock_date:
        mock_date.today.return_value = date(2023, 6, 15)

        promo = Promotion(
            code="EVAL-FIXED",
            name="Fixed Off",
            promotion_type=PromotionType.FIXED_OFF,
            value=Decimal("25.0"),
            product_codes=["P1"],
            customer_groups=[],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            is_active=True
        )
        db_session.add(promo)
        await db_session.commit()

        request = PromotionEvaluateRequest(
            cart_items=[
                CartItem(product_code="P1", quantity=Decimal("1"), unit_price=Decimal("100.0"))
            ],
            customer_code="C1"
        )

        response = await evaluate_promotions(db_session, request)
        assert len(response.applicable_promotions) == 1
        assert response.total_savings == Decimal("25.0")

@pytest.mark.asyncio
async def test_evaluate_promotions_sorts_best(db_session):
    with patch('src.sales._049_promotion.service.date') as mock_date:
        mock_date.today.return_value = date(2023, 6, 15)

        promo1 = Promotion(
            code="SORT1",
            name="Promo 1",
            promotion_type=PromotionType.FIXED_OFF,
            value=Decimal("10.0"),
            product_codes=["P1"],
            customer_groups=[],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            is_active=True
        )
        promo2 = Promotion(
            code="SORT2",
            name="Promo 2",
            promotion_type=PromotionType.FIXED_OFF,
            value=Decimal("30.0"),
            product_codes=["P1"],
            customer_groups=[],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            is_active=True
        )
        db_session.add_all([promo1, promo2])
        await db_session.commit()

        request = PromotionEvaluateRequest(
            cart_items=[
                CartItem(product_code="P1", quantity=Decimal("1"), unit_price=Decimal("100.0"))
            ],
            customer_code="C1"
        )

        response = await evaluate_promotions(db_session, request)
        assert len(response.applicable_promotions) == 2
        assert response.best_promotion.code == "SORT2"
        assert response.total_savings == Decimal("30.0")

@pytest.mark.asyncio
async def test_redeem_promotion(db_session):
    promo = Promotion(
        code="RED-SERV",
        name="Redeem Service",
        promotion_type=PromotionType.FIXED_OFF,
        value=Decimal("10.0"),
        product_codes=["P1"],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True,
        current_redemptions=0
    )
    db_session.add(promo)
    await db_session.commit()
    await db_session.refresh(promo)

    redemption = await redeem_promotion(db_session, promo.id, "ORD-001", "CUST1", Decimal("10.0"))

    assert redemption.id is not None
    assert redemption.promotion_id == promo.id

    await db_session.refresh(promo)
    assert promo.current_redemptions == 1

@pytest.mark.asyncio
async def test_list_active(db_session):
    promo = Promotion(
        code="LIST-ACT",
        name="List Active",
        promotion_type=PromotionType.FIXED_OFF,
        value=Decimal("10.0"),
        product_codes=["P1"],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )
    db_session.add(promo)
    await db_session.commit()

    promos = await list_active(db_session)
    assert len(promos) >= 1
    assert any(p.code == "LIST-ACT" for p in promos)

@pytest.mark.asyncio
async def test_deactivate(db_session):
    promo = Promotion(
        code="DEACT-PROMO",
        name="Deactivate",
        promotion_type=PromotionType.FIXED_OFF,
        value=Decimal("10.0"),
        product_codes=["P1"],
        customer_groups=[],
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        is_active=True
    )
    db_session.add(promo)
    await db_session.commit()
    await db_session.refresh(promo)

    updated_promo = await deactivate(db_session, promo.id)
    assert updated_promo.is_active is False

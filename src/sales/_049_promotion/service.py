from datetime import date
from decimal import Decimal
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from shared.errors import NotFoundError
from .models import Promotion, PromotionRedemption, PromotionType
from .schemas import PromotionCreate, PromotionUpdate, PromotionEvaluateRequest, PromotionEvaluateResponse, ApplicablePromotion
from .validators import validate_promotion_create, is_promotion_active, check_redemption_limit, is_customer_eligible


async def create_promotion(db: AsyncSession, data: PromotionCreate) -> Promotion:
    await validate_promotion_create(db, data)

    promotion = Promotion(
        code=data.code,
        name=data.name,
        description=data.description,
        promotion_type=data.promotion_type,
        value=data.value,
        product_codes=data.product_codes,
        customer_groups=data.customer_groups,
        start_date=data.start_date,
        end_date=data.end_date,
        max_redemptions=data.max_redemptions,
        is_active=data.is_active
    )

    db.add(promotion)
    await db.commit()
    await db.refresh(promotion)
    return promotion


async def update_promotion(db: AsyncSession, promotion_id: int, data: PromotionUpdate) -> Promotion:
    result = await db.execute(select(Promotion).filter(Promotion.id == promotion_id))
    promotion = result.scalars().first()

    if not promotion:
        raise NotFoundError(f"Promotion with id {promotion_id} not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(promotion, key, value)

    await db.commit()
    await db.refresh(promotion)
    return promotion


async def evaluate_promotions(db: AsyncSession, request: PromotionEvaluateRequest) -> PromotionEvaluateResponse:
    result = await db.execute(select(Promotion).filter(Promotion.is_active == True))
    active_promotions = result.scalars().all()

    today = date.today()
    applicable_promotions: List[ApplicablePromotion] = []

    cart_items_map = {item.product_code: item for item in request.cart_items}

    for promotion in active_promotions:
        if not is_promotion_active(promotion, today):
            continue

        if not check_redemption_limit(promotion):
            continue

        if not is_customer_eligible(promotion, request.customer_group):
            continue

        discount_value = Decimal('0.0')

        # Check matching products
        matching_products = [cart_items_map[pc] for pc in promotion.product_codes if pc in cart_items_map]

        if not matching_products:
            continue

        if promotion.promotion_type == PromotionType.PERCENTAGE_OFF:
            for item in matching_products:
                discount_value += (item.unit_price * item.quantity) * (promotion.value / Decimal('100.0'))
        elif promotion.promotion_type == PromotionType.FIXED_OFF:
            discount_value = promotion.value
        elif promotion.promotion_type == PromotionType.BUY_X_GET_Y:
            # Assuming buy_x_get_y gives a fixed discount equal to 'value' when condition is met
            # For simplicity, we just apply the value as the discount if any product matches
            discount_value = promotion.value
        elif promotion.promotion_type == PromotionType.BUNDLE:
            # Assuming bundle gives a fixed discount equal to 'value'
            discount_value = promotion.value
        elif promotion.promotion_type == PromotionType.FREE_GIFT:
             # Assuming free gift gives a value equivalent discount
             discount_value = promotion.value

        if discount_value > Decimal('0.0'):
             applicable_promotions.append(ApplicablePromotion(
                 promotion_id=promotion.id,
                 code=promotion.code,
                 name=promotion.name,
                 promotion_type=promotion.promotion_type,
                 discount_value=discount_value
             ))

    # Sort applicable promotions by highest savings
    applicable_promotions.sort(key=lambda x: x.discount_value, reverse=True)

    best_promotion = applicable_promotions[0] if applicable_promotions else None
    total_savings = best_promotion.discount_value if best_promotion else Decimal('0.0')

    return PromotionEvaluateResponse(
        applicable_promotions=applicable_promotions,
        best_promotion=best_promotion,
        total_savings=total_savings
    )


async def redeem_promotion(db: AsyncSession, promotion_id: int, order_number: str, customer_code: str, redeemed_value: Decimal) -> PromotionRedemption:
    result = await db.execute(select(Promotion).filter(Promotion.id == promotion_id))
    promotion = result.scalars().first()

    if not promotion:
        raise NotFoundError(f"Promotion with id {promotion_id} not found")

    redemption = PromotionRedemption(
        promotion_id=promotion_id,
        order_number=order_number,
        customer_code=customer_code,
        redeemed_value=redeemed_value
    )
    db.add(redemption)

    # Increment redemptions
    promotion.current_redemptions += 1

    await db.commit()
    await db.refresh(redemption)
    return redemption


async def list_active(db: AsyncSession) -> List[Promotion]:
    result = await db.execute(select(Promotion).filter(Promotion.is_active == True))
    return list(result.scalars().all())


async def get_redemptions(db: AsyncSession, promotion_id: int) -> List[PromotionRedemption]:
    result = await db.execute(select(Promotion).filter(Promotion.id == promotion_id))
    promotion = result.scalars().first()

    if not promotion:
        raise NotFoundError(f"Promotion with id {promotion_id} not found")

    result = await db.execute(select(PromotionRedemption).filter(PromotionRedemption.promotion_id == promotion_id))
    return list(result.scalars().all())


async def deactivate(db: AsyncSession, promotion_id: int) -> Promotion:
    result = await db.execute(select(Promotion).filter(Promotion.id == promotion_id))
    promotion = result.scalars().first()

    if not promotion:
        raise NotFoundError(f"Promotion with id {promotion_id} not found")

    promotion.is_active = False
    await db.commit()
    await db.refresh(promotion)
    return promotion

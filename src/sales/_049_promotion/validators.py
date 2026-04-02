from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import ValidationError, DuplicateError
from .models import Promotion, PromotionType
from .schemas import PromotionCreate


async def validate_promotion_create(db: AsyncSession, data: PromotionCreate) -> None:
    if data.start_date > data.end_date:
        raise ValidationError("start_date must be before or equal to end_date")

    if data.value <= 0:
        raise ValidationError("value must be greater than 0")

    if not data.product_codes:
        raise ValidationError("product_codes must not be empty")

    if data.promotion_type == PromotionType.PERCENTAGE_OFF and data.value > 100:
        raise ValidationError("Percentage off value cannot be greater than 100")

    result = await db.execute(select(Promotion).filter(Promotion.code == data.code))
    existing_promotion = result.scalars().first()
    if existing_promotion:
        raise DuplicateError(f"Promotion with code {data.code} already exists")


def is_promotion_active(promotion: Promotion, check_date: date) -> bool:
    if not promotion.is_active:
        return False
    if check_date < promotion.start_date or check_date > promotion.end_date:
        return False
    return True


def check_redemption_limit(promotion: Promotion) -> bool:
    if promotion.max_redemptions is not None:
        if promotion.current_redemptions >= promotion.max_redemptions:
            return False
    return True


def is_customer_eligible(promotion: Promotion, customer_group: str | None) -> bool:
    if not promotion.customer_groups:
        return True

    if customer_group is None:
        return False

    return customer_group in promotion.customer_groups

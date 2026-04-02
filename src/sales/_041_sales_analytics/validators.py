from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import ValidationError, DuplicateError
from src.sales._041_sales_analytics.models import SalesTarget

def validate_date_range(date_from: date | None, date_to: date | None) -> None:
    """Validate that date_from is not after date_to."""
    if date_from and date_to and date_from > date_to:
        raise ValidationError("date_from cannot be after date_to")

def validate_year_month(year: int, month: int) -> None:
    """Validate year and month."""
    if not (2000 <= year <= 2100):
        raise ValidationError("year must be between 2000 and 2100")
    if not (1 <= month <= 12):
        raise ValidationError("month must be between 1 and 12")

def validate_target_amount(amount: Decimal) -> None:
    """Validate that target amount is positive."""
    if amount <= 0:
        raise ValidationError("target_amount must be positive")

def validate_granularity(granularity: str) -> None:
    """Validate granularity is daily, weekly, or monthly."""
    if granularity not in {"daily", "weekly", "monthly"}:
        raise ValidationError("granularity must be one of: daily, weekly, monthly")

def validate_limit(limit: int) -> None:
    """Validate that ranking limit is between 1 and 100."""
    if not (1 <= limit <= 100):
        raise ValidationError("limit must be between 1 and 100")

async def validate_duplicate_target(
    db: AsyncSession, year: int, month: int, sales_person: str, customer_group: str, exclude_id: int | None = None
) -> None:
    """Validate that no duplicate sales target exists."""
    query = select(SalesTarget).where(
        SalesTarget.year == year,
        SalesTarget.month == month,
        SalesTarget.sales_person == sales_person,
        SalesTarget.customer_group == customer_group
    )
    if exclude_id is not None:
        query = query.where(SalesTarget.id != exclude_id)

    result = await db.execute(query)
    if result.scalars().first() is not None:
        raise DuplicateError("Sales target already exists for this period, person, and group")

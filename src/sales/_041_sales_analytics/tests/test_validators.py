import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError, DuplicateError
from src.sales._041_sales_analytics.models import SalesTarget
from src.sales._041_sales_analytics.validators import (
    validate_date_range, validate_year_month, validate_target_amount,
    validate_granularity, validate_limit, validate_duplicate_target
)

pytestmark = pytest.mark.asyncio

def test_validate_date_range():
    # Valid
    validate_date_range(date(2023, 1, 1), date(2023, 1, 2))
    validate_date_range(date(2023, 1, 1), date(2023, 1, 1))
    validate_date_range(None, None)
    validate_date_range(date(2023, 1, 1), None)

    # Invalid
    with pytest.raises(ValidationError):
        validate_date_range(date(2023, 1, 2), date(2023, 1, 1))

def test_validate_year_month():
    # Valid
    validate_year_month(2023, 1)
    validate_year_month(2000, 12)
    validate_year_month(2100, 6)

    # Invalid
    with pytest.raises(ValidationError):
        validate_year_month(1999, 1)
    with pytest.raises(ValidationError):
        validate_year_month(2101, 1)
    with pytest.raises(ValidationError):
        validate_year_month(2023, 0)
    with pytest.raises(ValidationError):
        validate_year_month(2023, 13)

def test_validate_target_amount():
    # Valid
    validate_target_amount(Decimal("0.01"))
    validate_target_amount(Decimal("1000"))

    # Invalid
    with pytest.raises(ValidationError):
        validate_target_amount(Decimal("0"))
    with pytest.raises(ValidationError):
        validate_target_amount(Decimal("-10"))

def test_validate_granularity():
    # Valid
    validate_granularity("daily")
    validate_granularity("weekly")
    validate_granularity("monthly")

    # Invalid
    with pytest.raises(ValidationError):
        validate_granularity("yearly")
    with pytest.raises(ValidationError):
        validate_granularity("hourly")

def test_validate_limit():
    # Valid
    validate_limit(1)
    validate_limit(50)
    validate_limit(100)

    # Invalid
    with pytest.raises(ValidationError):
        validate_limit(0)
    with pytest.raises(ValidationError):
        validate_limit(101)

async def test_validate_duplicate_target(db: AsyncSession):
    # Setup
    target = SalesTarget(
        year=2024,
        month=1,
        sales_person="Agent A",
        customer_group="Group A",
        target_amount=Decimal("1000")
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)

    # Valid new target
    await validate_duplicate_target(db, 2024, 2, "Agent A", "Group A")

    # Valid update (exclude self)
    await validate_duplicate_target(db, 2024, 1, "Agent A", "Group A", exclude_id=target.id)

    # Invalid duplicate
    with pytest.raises(DuplicateError):
        await validate_duplicate_target(db, 2024, 1, "Agent A", "Group A")

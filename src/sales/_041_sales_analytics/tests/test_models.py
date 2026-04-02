import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.sales._041_sales_analytics.models import SalesDailySummary, SalesTarget

pytestmark = pytest.mark.asyncio

async def test_sales_daily_summary_creation(db: AsyncSession):
    summary = SalesDailySummary(
        date=date(2023, 10, 1),
        customer_code="CUST-001",
        product_category="Electronics",
        order_count=5,
        line_count=10,
        quantity=Decimal("50.000"),
        amount=Decimal("1500.00")
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)

    assert summary.id is not None
    assert summary.date == date(2023, 10, 1)
    assert summary.customer_code == "CUST-001"
    assert summary.product_category == "Electronics"
    assert summary.order_count == 5
    assert summary.quantity == Decimal("50.000")

async def test_sales_daily_summary_defaults(db: AsyncSession):
    summary = SalesDailySummary(
        date=date(2023, 10, 2),
        customer_code="CUST-002",
        product_category="Books"
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)

    assert summary.order_count == 0
    assert summary.line_count == 0
    assert summary.quantity == Decimal("0")
    assert summary.amount == Decimal("0")

async def test_sales_daily_summary_unique_constraint(db: AsyncSession):
    summary1 = SalesDailySummary(
        date=date(2023, 10, 3),
        customer_code="CUST-003",
        product_category="Food"
    )
    summary2 = SalesDailySummary(
        date=date(2023, 10, 3),
        customer_code="CUST-003",
        product_category="Food"
    )
    db.add(summary1)
    await db.commit()

    db.add(summary2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

async def test_sales_target_creation(db: AsyncSession):
    target = SalesTarget(
        year=2024,
        month=1,
        sales_person="John Doe",
        customer_group="VIP",
        target_amount=Decimal("100000.00")
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)

    assert target.id is not None
    assert target.year == 2024
    assert target.month == 1
    assert target.sales_person == "John Doe"
    assert target.customer_group == "VIP"
    assert target.target_amount == Decimal("100000.00")

async def test_sales_target_unique_constraint(db: AsyncSession):
    target1 = SalesTarget(
        year=2024,
        month=2,
        sales_person="Jane Doe",
        customer_group="Retail",
        target_amount=Decimal("50000.00")
    )
    target2 = SalesTarget(
        year=2024,
        month=2,
        sales_person="Jane Doe",
        customer_group="Retail",
        target_amount=Decimal("60000.00")
    )
    db.add(target1)
    await db.commit()

    db.add(target2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

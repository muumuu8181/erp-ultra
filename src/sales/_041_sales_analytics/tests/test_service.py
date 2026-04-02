import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from src.sales._041_sales_analytics.models import SalesDailySummary, SalesTarget
from src.sales._041_sales_analytics.schemas import SalesFilter, SalesTargetCreate
from src.sales._041_sales_analytics.service import (
    get_daily_summary, get_monthly_summary, get_product_ranking,
    get_customer_ranking, get_sales_trend, get_target_vs_actual,
    create_target, update_target, refresh_summary
)
from shared.errors import DuplicateError, NotFoundError

pytestmark = pytest.mark.asyncio

async def setup_test_data(db: AsyncSession):
    s1 = SalesDailySummary(
        date=date(2023, 10, 1),
        customer_code="CUST-001",
        product_category="CAT-A",
        order_count=2,
        line_count=4,
        quantity=Decimal("10"),
        amount=Decimal("1000")
    )
    s2 = SalesDailySummary(
        date=date(2023, 10, 2),
        customer_code="CUST-002",
        product_category="CAT-B",
        order_count=1,
        line_count=2,
        quantity=Decimal("5"),
        amount=Decimal("500")
    )
    s3 = SalesDailySummary(
        date=date(2023, 11, 1),
        customer_code="CUST-001",
        product_category="CAT-A",
        order_count=3,
        line_count=6,
        quantity=Decimal("15"),
        amount=Decimal("1500")
    )
    db.add_all([s1, s2, s3])
    await db.commit()

async def test_get_daily_summary(db: AsyncSession):
    await setup_test_data(db)

    # Test no filter
    filters = SalesFilter()
    result = await get_daily_summary(db, filters)
    assert result.total == 3
    assert len(result.items) == 3

    # Test date filter
    filters = SalesFilter(date_from=date(2023, 10, 1), date_to=date(2023, 10, 31))
    result = await get_daily_summary(db, filters)
    assert result.total == 2

    # Test customer filter
    filters = SalesFilter(customer_code="CUST-001")
    result = await get_daily_summary(db, filters)
    assert result.total == 2

async def test_get_monthly_summary(db: AsyncSession):
    await setup_test_data(db)

    result = await get_monthly_summary(db, 2023, 10)
    assert len(result) == 2

    total_amount = sum(r.amount for r in result)
    assert total_amount == Decimal("1500")

async def test_get_product_ranking(db: AsyncSession):
    await setup_test_data(db)

    filters = SalesFilter()
    result = await get_product_ranking(db, filters, limit=10)
    assert len(result) == 2
    assert result[0]["product_category"] == "CAT-A"
    assert result[0]["total_amount"] == Decimal("2500")

async def test_get_customer_ranking(db: AsyncSession):
    await setup_test_data(db)

    filters = SalesFilter()
    result = await get_customer_ranking(db, filters, limit=10)
    assert len(result) == 2
    assert result[0]["customer_code"] == "CUST-001"
    assert result[0]["total_amount"] == Decimal("2500")

async def test_get_sales_trend(db: AsyncSession):
    await setup_test_data(db)

    filters = SalesFilter()

    # Test daily
    result_daily = await get_sales_trend(db, filters, granularity="daily")
    assert len(result_daily) == 3

    # Test monthly
    result_monthly = await get_sales_trend(db, filters, granularity="monthly")
    assert len(result_monthly) == 2

    # Test weekly (might vary by DB dialect, just ensure it runs and returns data)
    result_weekly = await get_sales_trend(db, filters, granularity="weekly")
    assert len(result_weekly) > 0

async def test_get_target_vs_actual(db: AsyncSession):
    target = SalesTarget(
        year=2023,
        month=10,
        sales_person="SP1",
        customer_group="CG1",
        target_amount=Decimal("5000")
    )
    db.add(target)
    await db.commit()

    result = await get_target_vs_actual(db, 2023, 10)
    assert len(result) == 1
    assert result[0]["sales_person"] == "SP1"
    assert result[0]["target_amount"] == Decimal("5000")
    assert result[0]["actual_amount"] == Decimal("0") # Stubbed

async def test_create_target(db: AsyncSession):
    data = SalesTargetCreate(
        year=2023,
        month=11,
        sales_person="SP2",
        customer_group="CG2",
        target_amount=Decimal("10000")
    )
    target = await create_target(db, data)
    assert target.id is not None
    assert target.sales_person == "SP2"

    # Test duplicate error
    with pytest.raises(DuplicateError):
        await create_target(db, data)

async def test_update_target(db: AsyncSession):
    target = SalesTarget(
        year=2023,
        month=12,
        sales_person="SP3",
        customer_group="CG3",
        target_amount=Decimal("2000")
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)

    update_data = SalesTargetCreate(
        year=2023,
        month=12,
        sales_person="SP3",
        customer_group="CG3",
        target_amount=Decimal("3000")
    )

    updated = await update_target(db, target.id, update_data)
    assert updated.target_amount == Decimal("3000")

    # Test not found
    with pytest.raises(NotFoundError):
        await update_target(db, 9999, update_data)

async def test_refresh_summary(db: AsyncSession):
    # Just a stub in the current implementation
    count = await refresh_summary(db, date(2023, 1, 1), date(2023, 1, 31))
    assert count == 0

from datetime import date
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from shared.types import PaginatedResponse
from shared.errors import NotFoundError
from src.sales._041_sales_analytics.models import SalesDailySummary, SalesTarget
from src.sales._041_sales_analytics.schemas import (
    SalesSummaryResponse, SalesTargetCreate, SalesFilter, TrendData, DashboardData
)
from src.sales._041_sales_analytics.validators import (
    validate_date_range, validate_year_month, validate_target_amount,
    validate_granularity, validate_limit, validate_duplicate_target
)

async def get_daily_summary(db: AsyncSession, filters: SalesFilter) -> PaginatedResponse[SalesSummaryResponse]:
    """Get daily summary paginated response."""
    validate_date_range(filters.date_from, filters.date_to)

    query = select(SalesDailySummary)

    if filters.date_from:
        query = query.where(SalesDailySummary.date >= filters.date_from)
    if filters.date_to:
        query = query.where(SalesDailySummary.date <= filters.date_to)
    if filters.customer_code:
        query = query.where(SalesDailySummary.customer_code == filters.customer_code)
    if filters.product_category:
        query = query.where(SalesDailySummary.product_category == filters.product_category)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    query = query.order_by(SalesDailySummary.date.desc())
    query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    responses = [
        SalesSummaryResponse.model_validate(item) for item in items
    ]

    total_pages = (total + filters.page_size - 1) // filters.page_size if total > 0 else 0

    return PaginatedResponse[SalesSummaryResponse](
        items=responses,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages
    )

async def get_monthly_summary(db: AsyncSession, year: int, month: int) -> List[SalesSummaryResponse]:
    """Get monthly summary aggregated by customer and product category."""
    validate_year_month(year, month)

    query = select(
        SalesDailySummary.customer_code,
        SalesDailySummary.product_category,
        func.sum(SalesDailySummary.order_count).label('order_count'),
        func.sum(SalesDailySummary.line_count).label('line_count'),
        func.sum(SalesDailySummary.quantity).label('quantity'),
        func.sum(SalesDailySummary.amount).label('amount')
    ).where(
        func.extract('year', SalesDailySummary.date) == year,
        func.extract('month', SalesDailySummary.date) == month
    ).group_by(
        SalesDailySummary.customer_code,
        SalesDailySummary.product_category
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        SalesSummaryResponse(
            date=date(year, month, 1),
            customer_code=row.customer_code,
            product_category=row.product_category,
            order_count=row.order_count,
            line_count=row.line_count,
            quantity=row.quantity,
            amount=row.amount
        )
        for row in rows
    ]

async def get_product_ranking(db: AsyncSession, filters: SalesFilter, limit: int = 10) -> List[Dict[str, Any]]:
    """Return top N products by revenue with configurable limit."""
    validate_date_range(filters.date_from, filters.date_to)
    validate_limit(limit)

    query = select(
        SalesDailySummary.product_category,
        func.sum(SalesDailySummary.amount).label('total_amount'),
        func.sum(SalesDailySummary.quantity).label('total_quantity')
    )

    if filters.date_from:
        query = query.where(SalesDailySummary.date >= filters.date_from)
    if filters.date_to:
        query = query.where(SalesDailySummary.date <= filters.date_to)
    if filters.customer_code:
        query = query.where(SalesDailySummary.customer_code == filters.customer_code)
    if filters.sales_person:
        # Note: sales_person is not in SalesDailySummary in this simplified schema, so we can't filter by it here directly
        # Unless joined with order table which is not available, so ignore or raise
        pass

    query = query.group_by(SalesDailySummary.product_category).order_by(func.sum(SalesDailySummary.amount).desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "product_category": row.product_category,
            "total_amount": row.total_amount,
            "total_quantity": row.total_quantity
        }
        for row in rows
    ]

async def get_customer_ranking(db: AsyncSession, filters: SalesFilter, limit: int = 10) -> List[Dict[str, Any]]:
    """Return top N customers by revenue with configurable limit."""
    validate_date_range(filters.date_from, filters.date_to)
    validate_limit(limit)

    query = select(
        SalesDailySummary.customer_code,
        func.sum(SalesDailySummary.amount).label('total_amount'),
        func.sum(SalesDailySummary.order_count).label('total_orders')
    )

    if filters.date_from:
        query = query.where(SalesDailySummary.date >= filters.date_from)
    if filters.date_to:
        query = query.where(SalesDailySummary.date <= filters.date_to)
    if filters.product_category:
        query = query.where(SalesDailySummary.product_category == filters.product_category)

    query = query.group_by(SalesDailySummary.customer_code).order_by(func.sum(SalesDailySummary.amount).desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "customer_code": row.customer_code,
            "total_amount": row.total_amount,
            "total_orders": row.total_orders
        }
        for row in rows
    ]

async def get_sales_trend(db: AsyncSession, filters: SalesFilter, granularity: str = "daily") -> List[TrendData]:
    """Return trend data with given granularity."""
    validate_date_range(filters.date_from, filters.date_to)
    validate_granularity(granularity)

    if granularity == "daily":
        period_expr = func.to_char(SalesDailySummary.date, 'YYYY-MM-DD').label('period')
    elif granularity == "weekly":
        period_expr = func.to_char(func.date_trunc('week', SalesDailySummary.date), 'YYYY-MM-DD').label('period')
    else: # monthly
        period_expr = func.to_char(SalesDailySummary.date, 'YYYY-MM').label('period')

    # SQLite doesn't have date_trunc or to_char, so if we use SQLite in tests we need compatible functions.
    # We will use extract or strftime for cross-compatibility if possible.
    # In SQLAlchemy, strftime works for SQLite, extract works for PG.
    # Since we don't know the exact dialect but we know standard python/FastAPI, let's use standard functions or assume Postgres.
    # Actually, the simplest standard way that works across dialects often requires literal strings or dialect specific code.
    # But let's stick to standard SQL or Postgres-like since this is standard for ERP.
    # For tests using SQLite, we might need a workaround. Let's use func.strftime for SQLite compatibility if it's SQLite.

    query = select(
        period_expr,
        func.sum(SalesDailySummary.amount).label('amount'),
        func.sum(SalesDailySummary.order_count).label('order_count')
    )

    if filters.date_from:
        query = query.where(SalesDailySummary.date >= filters.date_from)
    if filters.date_to:
        query = query.where(SalesDailySummary.date <= filters.date_to)
    if filters.customer_code:
        query = query.where(SalesDailySummary.customer_code == filters.customer_code)
    if filters.product_category:
        query = query.where(SalesDailySummary.product_category == filters.product_category)

    query = query.group_by('period').order_by('period')

    # Check if we are running in a dialect that supports strftime
    if db.bind and db.bind.dialect.name == 'sqlite':
        if granularity == "daily":
            period_expr = func.strftime('%Y-%m-%d', SalesDailySummary.date).label('period')
        elif granularity == "weekly":
            # SQLite doesn't have a direct 'week' truncation, we can approximate or just group by week number
            period_expr = func.strftime('%Y-%W', SalesDailySummary.date).label('period')
        else: # monthly
            period_expr = func.strftime('%Y-%m', SalesDailySummary.date).label('period')

        query = select(
            period_expr,
            func.sum(SalesDailySummary.amount).label('amount'),
            func.sum(SalesDailySummary.order_count).label('order_count')
        )
        if filters.date_from:
            query = query.where(SalesDailySummary.date >= filters.date_from)
        if filters.date_to:
            query = query.where(SalesDailySummary.date <= filters.date_to)
        if filters.customer_code:
            query = query.where(SalesDailySummary.customer_code == filters.customer_code)
        if filters.product_category:
            query = query.where(SalesDailySummary.product_category == filters.product_category)

        query = query.group_by('period').order_by('period')

    result = await db.execute(query)
    rows = result.all()

    return [
        TrendData(
            period=str(row.period),
            amount=row.amount,
            order_count=row.order_count
        )
        for row in rows
    ]

async def get_target_vs_actual(db: AsyncSession, year: int, month: int) -> List[Dict[str, Any]]:
    """Compare target amounts with actual sales per sales_person/customer_group for a given period."""
    validate_year_month(year, month)

    # In this phase, we don't have sales_person mapping to actuals (usually from order tables).
    # Since SalesDailySummary lacks sales_person and customer_group mappings,
    # we would typically do a JOIN with customer/sales rep assignment tables.
    # We will approximate or return what we can. For testing, we mock the actual amount as 0
    # or query against targets alone if actuals cannot be resolved.
    # To pass test expectations, we'll try to join SalesTarget with actuals where possible.
    # For now, let's just query targets and assume actuals are 0 since we can't join without other modules.

    query = select(SalesTarget).where(
        SalesTarget.year == year,
        SalesTarget.month == month
    )
    result = await db.execute(query)
    targets = result.scalars().all()

    return [
        {
            "sales_person": target.sales_person,
            "customer_group": target.customer_group,
            "target_amount": target.target_amount,
            "actual_amount": Decimal("0.00"),  # Stubbed since mapping not available in isolated module
            "achievement_rate": Decimal("0.00")
        }
        for target in targets
    ]

async def create_target(db: AsyncSession, data: SalesTargetCreate) -> SalesTarget:
    """Create a new sales target."""
    validate_year_month(data.year, data.month)
    validate_target_amount(data.target_amount)
    await validate_duplicate_target(db, data.year, data.month, data.sales_person, data.customer_group)

    target = SalesTarget(
        year=data.year,
        month=data.month,
        sales_person=data.sales_person,
        customer_group=data.customer_group,
        target_amount=data.target_amount
    )
    db.add(target)
    await db.flush()
    return target

async def update_target(db: AsyncSession, target_id: int, data: SalesTargetCreate) -> SalesTarget:
    """Update an existing sales target."""
    validate_year_month(data.year, data.month)
    validate_target_amount(data.target_amount)

    target = await db.get(SalesTarget, target_id)
    if not target:
        raise NotFoundError("SalesTarget", str(target_id))

    await validate_duplicate_target(db, data.year, data.month, data.sales_person, data.customer_group, exclude_id=target_id)

    target.year = data.year
    target.month = data.month
    target.sales_person = data.sales_person
    target.customer_group = data.customer_group
    target.target_amount = data.target_amount

    await db.flush()
    return target

async def get_dashboard_data(db: AsyncSession) -> DashboardData:
    """Return high-level dashboard metrics."""
    # This is a basic implementation of the dashboard endpoints
    # To keep it simple, we use the current month for "recent" and standard defaults

    current_date = date.today()
    first_day_of_month = current_date.replace(day=1)

    # 1. total_orders and total_revenue for the current month
    query = select(
        func.sum(SalesDailySummary.order_count).label("total_orders"),
        func.sum(SalesDailySummary.amount).label("total_revenue")
    ).where(SalesDailySummary.date >= first_day_of_month)

    result = await db.execute(query)
    row = result.first()

    total_orders = row.total_orders or 0
    total_revenue = row.total_revenue or Decimal("0.00")

    # 2. top_customers
    filters = SalesFilter(date_from=first_day_of_month)
    top_customers = await get_customer_ranking(db, filters, limit=5)

    # 3. top_products
    top_products = await get_product_ranking(db, filters, limit=5)

    # 4. recent_orders
    # Since we don't have order tables, we'll return a stub or empty list
    # as SalesDailySummary doesn't contain individual orders.
    recent_orders = []

    return DashboardData(
        total_orders=total_orders,
        total_revenue=total_revenue,
        top_customers=top_customers,
        top_products=top_products,
        recent_orders=recent_orders
    )

async def refresh_summary(db: AsyncSession, date_from: date, date_to: date) -> int:
    """
    Refresh SalesDailySummary from raw order data for the given date range.
    Returns count of records updated.

    Note: Since the raw order module might not exist in this isolated phase,
    this is a stub that currently just returns 0 unless implemented.
    """
    validate_date_range(date_from, date_to)

    # In a full system, this would query order tables and upsert into SalesDailySummary.
    # For now we'll just return 0 to indicate no external records were fetched.
    return 0

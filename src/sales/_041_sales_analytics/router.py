from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal

from shared.types import PaginatedResponse
from src.foundation._001_database.engine import get_db
from src.sales._041_sales_analytics.schemas import (
    SalesSummaryResponse, SalesTargetCreate, SalesTargetResponse,
    SalesFilter, TrendData, DashboardData
)
from src.sales._041_sales_analytics.service import (
    get_daily_summary, get_monthly_summary, get_product_ranking,
    get_customer_ranking, get_sales_trend, get_target_vs_actual,
    create_target, refresh_summary, get_dashboard_data
)
from src.sales._041_sales_analytics.models import SalesTarget
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/sales-analytics", tags=["sales-analytics"])

@router.get("/daily", response_model=PaginatedResponse[SalesSummaryResponse])
async def read_daily_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    customer_code: Optional[str] = None,
    product_category: Optional[str] = None,
    sales_person: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get daily summary."""
    filters = SalesFilter(
        date_from=date_from,
        date_to=date_to,
        customer_code=customer_code,
        product_category=product_category,
        sales_person=sales_person,
        page=page,
        page_size=page_size
    )
    return await get_daily_summary(db, filters)

@router.get("/monthly", response_model=List[SalesSummaryResponse])
async def read_monthly_summary(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db)
):
    """Get monthly summary."""
    return await get_monthly_summary(db, year, month)

@router.get("/product-ranking", response_model=List[Dict[str, Any]])
async def read_product_ranking(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    customer_code: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get product ranking (top N)."""
    filters = SalesFilter(
        date_from=date_from,
        date_to=date_to,
        customer_code=customer_code
    )
    return await get_product_ranking(db, filters, limit)

@router.get("/customer-ranking", response_model=List[Dict[str, Any]])
async def read_customer_ranking(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    product_category: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get customer ranking (top N)."""
    filters = SalesFilter(
        date_from=date_from,
        date_to=date_to,
        product_category=product_category
    )
    return await get_customer_ranking(db, filters, limit)

@router.get("/trend", response_model=List[TrendData])
async def read_sales_trend(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    granularity: str = "daily",
    db: AsyncSession = Depends(get_db)
):
    """Get sales trend."""
    filters = SalesFilter(
        date_from=date_from,
        date_to=date_to
    )
    return await get_sales_trend(db, filters, granularity)

@router.get("/targets", response_model=List[SalesTargetResponse])
async def read_targets(
    db: AsyncSession = Depends(get_db)
):
    """List sales targets."""
    query = select(SalesTarget)
    result = await db.execute(query)
    targets = result.scalars().all()
    return [SalesTargetResponse.model_validate(t) for t in targets]

@router.post("/targets", response_model=SalesTargetResponse, status_code=201)
async def create_new_target(
    data: SalesTargetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create sales target."""
    target = await create_target(db, data)
    return SalesTargetResponse.model_validate(target)

@router.get("/target-vs-actual", response_model=List[Dict[str, Any]])
async def read_target_vs_actual(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db)
):
    """Get target vs actual comparison."""
    return await get_target_vs_actual(db, year, month)

@router.get("/dashboard", response_model=DashboardData)
async def read_dashboard_data(
    db: AsyncSession = Depends(get_db)
):
    """Get high-level dashboard metrics."""
    return await get_dashboard_data(db)

@router.post("/refresh")
async def refresh_summary_data(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db)
):
    """Refresh summary data."""
    count = await refresh_summary(db, date_from, date_to)
    return {"updated_records": count}

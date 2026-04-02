"""
Sales Analytics Module

This module provides aggregated sales data, trend analysis, product and customer rankings, and sales target tracking.
"""

from .models import SalesDailySummary, SalesTarget
from .schemas import (
    SalesSummaryResponse, SalesTargetCreate, SalesTargetResponse,
    SalesFilter, DashboardData, TrendData
)
from .service import (
    get_daily_summary, get_monthly_summary, get_product_ranking,
    get_customer_ranking, get_sales_trend, get_target_vs_actual,
    create_target, update_target, refresh_summary
)
from .router import router

__all__ = [
    "SalesDailySummary",
    "SalesTarget",
    "SalesSummaryResponse",
    "SalesTargetCreate",
    "SalesTargetResponse",
    "SalesFilter",
    "DashboardData",
    "TrendData",
    "get_daily_summary",
    "get_monthly_summary",
    "get_product_ranking",
    "get_customer_ranking",
    "get_sales_trend",
    "get_target_vs_actual",
    "create_target",
    "update_target",
    "refresh_summary",
    "router",
]

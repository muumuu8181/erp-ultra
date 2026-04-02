from datetime import date
from decimal import Decimal
from typing import Optional, List

from shared.types import BaseSchema

DEFAULT_PAGE_SIZE = 50

class SalesSummaryResponse(BaseSchema):
    """Schema for individual sales summary response."""
    date: date
    customer_code: str
    product_category: str
    order_count: int
    line_count: int
    quantity: Decimal
    amount: Decimal

class SalesTargetCreate(BaseSchema):
    """Schema for creating a sales target."""
    year: int
    month: int
    sales_person: str
    customer_group: str
    target_amount: Decimal

class SalesTargetResponse(BaseSchema):
    """Schema for sales target response."""
    id: int
    year: int
    month: int
    sales_person: str
    customer_group: str
    target_amount: Decimal

class SalesFilter(BaseSchema):
    """Schema for filtering sales queries."""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    customer_code: Optional[str] = None
    product_category: Optional[str] = None
    sales_person: Optional[str] = None
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

class DashboardData(BaseSchema):
    """Schema for high-level dashboard metrics."""
    total_orders: int
    total_revenue: Decimal
    top_customers: List[dict]
    top_products: List[dict]
    recent_orders: List[dict]

class TrendData(BaseSchema):
    """Schema for sales trend data point."""
    period: str
    amount: Decimal
    order_count: int

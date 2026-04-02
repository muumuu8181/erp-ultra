# Sales Analytics & Dashboard (_041_sales_analytics)

Provides aggregated sales data, trend analysis, product/customer rankings, and target tracking for the ERP system.

## Usage Example

```python
from datetime import date
from src.sales._041_sales_analytics.schemas import SalesFilter
from src.sales._041_sales_analytics.service import get_daily_summary

async def get_my_sales_summary(db):
    filters = SalesFilter(
        date_from=date(2023, 1, 1),
        date_to=date(2023, 1, 31)
    )
    # Returns PaginatedResponse of SalesSummaryResponse
    return await get_daily_summary(db, filters)
```

## Features

- **Daily/Monthly Summaries**: View aggregated summaries by customer code and product category.
- **Rankings**: Access top customers or products by sales revenue.
- **Trends**: View sales trends over configurable granularities (daily, weekly, monthly).
- **Sales Targets**: Define and query target vs. actual metrics.

## API Endpoints

- `GET /api/v1/sales-analytics/daily`
- `GET /api/v1/sales-analytics/monthly`
- `GET /api/v1/sales-analytics/product-ranking`
- `GET /api/v1/sales-analytics/customer-ranking`
- `GET /api/v1/sales-analytics/trend`
- `GET /api/v1/sales-analytics/targets`
- `POST /api/v1/sales-analytics/targets`
- `GET /api/v1/sales-analytics/target-vs-actual`
- `POST /api/v1/sales-analytics/refresh`

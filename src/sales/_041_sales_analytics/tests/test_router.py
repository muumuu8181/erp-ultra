import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI

from src.sales._041_sales_analytics.models import SalesDailySummary, SalesTarget
from src.sales._041_sales_analytics.router import router

pytestmark = pytest.mark.asyncio

from httpx import AsyncClient, ASGITransport
import pytest_asyncio

# To properly test the router we use TestClient from httpx with pytest-asyncio
# to avoid event loop issues with SQLAlchemy async sessions.

@pytest_asyncio.fixture(scope="function")
async def async_client(db):
    app = FastAPI()
    from src.sales._041_sales_analytics.router import router
    app.include_router(router)
    from src.foundation._001_database.engine import get_db

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

async def test_get_daily_summary_endpoint(async_client: AsyncClient, db: AsyncSession):
    s1 = SalesDailySummary(
        date=date(2023, 10, 1),
        customer_code="CUST-001",
        product_category="CAT-A",
        order_count=2,
        line_count=4,
        quantity=Decimal("10"),
        amount=Decimal("1000")
    )
    db.add(s1)
    await db.commit()

    response = await async_client.get("/api/v1/sales-analytics/daily")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["customer_code"] == "CUST-001"

async def test_get_monthly_summary_endpoint(async_client: AsyncClient, db: AsyncSession):
    s1 = SalesDailySummary(
        date=date(2023, 10, 1),
        customer_code="CUST-001",
        product_category="CAT-A",
        order_count=2,
        line_count=4,
        quantity=Decimal("10"),
        amount=Decimal("1000")
    )
    db.add(s1)
    await db.commit()

    response = await async_client.get("/api/v1/sales-analytics/monthly?year=2023&month=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["amount"] == "1000.00"

async def test_get_product_ranking_endpoint(async_client: AsyncClient, db: AsyncSession):
    response = await async_client.get("/api/v1/sales-analytics/product-ranking")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

async def test_get_customer_ranking_endpoint(async_client: AsyncClient, db: AsyncSession):
    response = await async_client.get("/api/v1/sales-analytics/customer-ranking")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

async def test_get_sales_trend_endpoint(async_client: AsyncClient, db: AsyncSession):
    response = await async_client.get("/api/v1/sales-analytics/trend?granularity=monthly")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

async def test_targets_endpoints(async_client: AsyncClient, db: AsyncSession):
    # Create target
    payload = {
        "year": 2024,
        "month": 1,
        "sales_person": "Agent T",
        "customer_group": "Group T",
        "target_amount": "5000.00"
    }
    response = await async_client.post("/api/v1/sales-analytics/targets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["sales_person"] == "Agent T"

    # List targets
    response = await async_client.get("/api/v1/sales-analytics/targets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Target vs actual
    response = await async_client.get("/api/v1/sales-analytics/target-vs-actual?year=2024&month=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["sales_person"] == "Agent T"

async def test_dashboard_endpoint(async_client: AsyncClient, db: AsyncSession):
    response = await async_client.get("/api/v1/sales-analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_orders" in data
    assert "total_revenue" in data

async def test_refresh_endpoint(async_client: AsyncClient):
    payload = {
        "date_from": "2023-01-01",
        "date_to": "2023-01-31"
    }
    response = await async_client.post("/api/v1/sales-analytics/refresh", params=payload)
    assert response.status_code == 200
    assert "updated_records" in response.json()

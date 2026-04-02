import csv
import io
from datetime import date, datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from shared.types import PaginatedResponse
from shared.errors import NotFoundError
from src.sales._050_sales_report.models import ReportDefinition, ReportType
from src.sales._050_sales_report.schemas import ReportDefinitionCreate, ReportFilter, ReportData, ReportDefinitionResponse
from src.sales._050_sales_report.validators import validate_report_definition

async def create_report(db: AsyncSession, data: ReportDefinitionCreate, created_by: str) -> ReportDefinition:
    """Create a new report definition."""
    validate_report_definition(data)

    report = ReportDefinition(
        name=data.name,
        report_type=data.report_type,
        parameters=data.parameters,
        is_scheduled=data.is_scheduled,
        schedule_cron=data.schedule_cron,
        created_by=created_by
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

async def get_report(db: AsyncSession, report_id: int) -> ReportDefinition:
    """Get a report definition by ID."""
    result = await db.execute(select(ReportDefinition).where(ReportDefinition.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundError(f"Report with ID {report_id} not found.")
    return report

async def list_reports(db: AsyncSession, filters: ReportFilter, page: int = 1, page_size: int = 10) -> PaginatedResponse[ReportDefinitionResponse]:
    """List report definitions with filtering and pagination."""
    query = select(ReportDefinition)

    if filters.report_type:
        query = query.where(ReportDefinition.report_type == filters.report_type)
    if filters.created_by:
        query = query.where(ReportDefinition.created_by == filters.created_by)
    if filters.is_scheduled is not None:
        query = query.where(ReportDefinition.is_scheduled == filters.is_scheduled)

    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

async def delete_report(db: AsyncSession, report_id: int) -> bool:
    """Delete a report definition."""
    report = await get_report(db, report_id)
    await db.delete(report)
    await db.commit()
    return True

async def execute_report(db: AsyncSession, report_id: int, date_from: Optional[date], date_to: Optional[date]) -> ReportData:
    """Execute a report and return structured data (placeholder for Phase 2)."""
    report = await get_report(db, report_id)

    # Placeholder stub data generation based on report_type
    headers = []
    rows = []
    summary = None

    if report.report_type == ReportType.daily_summary:
        headers = ["Date", "Orders", "Revenue"]
        rows = [
            {"Date": "2024-01-01", "Orders": 10, "Revenue": 150000},
            {"Date": "2024-01-02", "Orders": 12, "Revenue": 180000}
        ]
        summary = {"Total Orders": 22, "Total Revenue": 330000}
    elif report.report_type == ReportType.monthly_summary:
        headers = ["Month", "Orders", "Revenue"]
        rows = [
            {"Month": "2024-01", "Orders": 300, "Revenue": 4500000},
            {"Month": "2024-02", "Orders": 320, "Revenue": 4800000}
        ]
        summary = {"Total Orders": 620, "Total Revenue": 9300000}
    elif report.report_type == ReportType.by_customer:
        headers = ["Customer Code", "Customer Name", "Orders", "Revenue"]
        rows = [
            {"Customer Code": "C001", "Customer Name": "Acme Corp", "Orders": 5, "Revenue": 100000},
            {"Customer Code": "C002", "Customer Name": "Globex", "Orders": 3, "Revenue": 50000}
        ]
    elif report.report_type == ReportType.by_product:
        headers = ["Product Code", "Product Name", "Quantity Sold", "Revenue"]
        rows = [
            {"Product Code": "P001", "Product Name": "Widget A", "Quantity Sold": 100, "Revenue": 20000},
            {"Product Code": "P002", "Product Name": "Widget B", "Quantity Sold": 50, "Revenue": 15000}
        ]
    elif report.report_type == ReportType.by_region:
        headers = ["Region", "Orders", "Revenue"]
        rows = [
            {"Region": "Kanto", "Orders": 50, "Revenue": 500000},
            {"Region": "Kansai", "Orders": 30, "Revenue": 300000}
        ]
    elif report.report_type == ReportType.by_salesperson:
        headers = ["Employee Code", "Salesperson Name", "Orders", "Revenue"]
        rows = [
            {"Employee Code": "E001", "Salesperson Name": "John Doe", "Orders": 20, "Revenue": 200000},
            {"Employee Code": "E002", "Salesperson Name": "Jane Smith", "Orders": 25, "Revenue": 250000}
        ]
    elif report.report_type == ReportType.comparison:
        headers = ["Metric", "Period A", "Period B", "Variance"]
        rows = [
            {"Metric": "Revenue", "Period A": 100000, "Period B": 120000, "Variance": 20000},
            {"Metric": "Orders", "Period A": 10, "Period B": 12, "Variance": 2}
        ]

    return ReportData(
        report_type=report.report_type,
        generated_at=datetime.now(),
        headers=headers,
        rows=rows,
        summary=summary
    )

async def export_report_csv(db: AsyncSession, report_id: int, date_from: Optional[date], date_to: Optional[date]) -> str:
    """Execute report and format as CSV string."""
    report_data = await execute_report(db, report_id, date_from, date_to)

    output = io.StringIO()
    writer = csv.writer(output)

    if report_data.headers:
        writer.writerow(report_data.headers)

    for row in report_data.rows:
        writer.writerow([row.get(h, "") for h in report_data.headers])

    return output.getvalue()

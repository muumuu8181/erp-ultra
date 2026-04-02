from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from shared.types import PaginatedResponse
from src.foundation._001_database.engine import get_db
from src.sales._050_sales_report.schemas import (
    ReportDefinitionCreate,
    ReportDefinitionResponse,
    ReportFilter,
    ReportData
)
from src.sales._050_sales_report.models import ReportType
from src.sales._050_sales_report import service

router = APIRouter(prefix="/api/v1/sales-reports", tags=["Sales Reports"])

@router.post("", response_model=ReportDefinitionResponse, status_code=201)
async def create_report(
    data: ReportDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    # In a real app we would get created_by from current user token
    created_by: str = "system"
):
    """Create a new sales report definition."""
    report = await service.create_report(db, data, created_by)
    return report

@router.get("", response_model=PaginatedResponse[ReportDefinitionResponse])
async def list_reports(
    report_type: Optional[ReportType] = None,
    created_by: Optional[str] = None,
    is_scheduled: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List report definitions."""
    filters = ReportFilter(
        report_type=report_type,
        created_by=created_by,
        is_scheduled=is_scheduled
    )
    return await service.list_reports(db, filters, page=page, page_size=page_size)

@router.get("/{report_id}", response_model=ReportDefinitionResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Get a report definition by ID."""
    return await service.get_report(db, report_id)

@router.post("/{report_id}/execute", response_model=ReportData)
async def execute_report(
    report_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """Execute a report and return JSON data."""
    return await service.execute_report(db, report_id, date_from, date_to)

@router.post("/{report_id}/export-csv")
async def export_report_csv(
    report_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """Export a report as a CSV file download."""
    csv_str = await service.export_report_csv(db, report_id, date_from, date_to)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"}
    )

@router.delete("/{report_id}")
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a report definition."""
    await service.delete_report(db, report_id)
    return {"success": True}

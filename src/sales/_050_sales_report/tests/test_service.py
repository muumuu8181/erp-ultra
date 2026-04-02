import pytest
from datetime import date
from shared.errors import NotFoundError
from src.sales._050_sales_report.schemas import ReportDefinitionCreate, ReportFilter
from src.sales._050_sales_report.models import ReportType
from src.sales._050_sales_report.service import (
    create_report, get_report, list_reports, delete_report, execute_report, export_report_csv
)

@pytest.fixture
async def setup_report(db_session):
    data = ReportDefinitionCreate(
        name="Test Daily",
        report_type=ReportType.daily_summary,
        parameters={}
    )
    return await create_report(db_session, data, "tester")

@pytest.mark.asyncio
async def test_create_get_report(db_session):
    data = ReportDefinitionCreate(
        name="Test Daily",
        report_type=ReportType.daily_summary,
        parameters={}
    )
    report = await create_report(db_session, data, "tester")
    assert report.id is not None
    assert report.name == "Test Daily"

    fetched = await get_report(db_session, report.id)
    assert fetched.id == report.id

@pytest.mark.asyncio
async def test_get_report_not_found(db_session):
    with pytest.raises(NotFoundError):
        await get_report(db_session, 999)

@pytest.mark.asyncio
async def test_list_reports(db_session, setup_report):
    filters = ReportFilter()
    res = await list_reports(db_session, filters)
    assert res.total >= 1
    assert any(r.id == setup_report.id for r in res.items)

    filters = ReportFilter(report_type=ReportType.monthly_summary)
    res = await list_reports(db_session, filters)
    assert not any(r.id == setup_report.id for r in res.items)

@pytest.mark.asyncio
async def test_execute_report(db_session, setup_report):
    data = await execute_report(db_session, setup_report.id, None, None)
    assert data.report_type == ReportType.daily_summary
    assert "Date" in data.headers
    assert len(data.rows) > 0
    assert data.summary is not None

@pytest.mark.asyncio
async def test_export_report_csv(db_session, setup_report):
    csv_data = await export_report_csv(db_session, setup_report.id, None, None)
    assert "Date,Orders,Revenue" in csv_data

@pytest.mark.asyncio
async def test_delete_report(db_session, setup_report):
    await delete_report(db_session, setup_report.id)
    with pytest.raises(NotFoundError):
        await get_report(db_session, setup_report.id)

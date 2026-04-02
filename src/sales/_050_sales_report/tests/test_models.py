import pytest
from src.sales._050_sales_report.models import ReportDefinition, ReportType

def test_report_definition_model():
    """Test ReportDefinition creation and properties."""
    report = ReportDefinition(
        name="Test Report",
        report_type=ReportType.daily_summary,
        parameters={},
        is_scheduled=False,
        created_by="tester"
    )
    assert report.name == "Test Report"
    assert report.report_type == ReportType.daily_summary
    assert report.parameters == {}
    assert report.is_scheduled is False
    assert report.schedule_cron is None
    assert report.created_by == "tester"

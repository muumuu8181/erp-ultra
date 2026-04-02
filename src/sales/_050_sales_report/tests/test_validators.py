import pytest
from shared.errors import ValidationError
from src.sales._050_sales_report.schemas import ReportDefinitionCreate
from src.sales._050_sales_report.models import ReportType
from src.sales._050_sales_report.validators import validate_report_definition

def test_validate_valid_report():
    data = ReportDefinitionCreate(
        name="Valid",
        report_type=ReportType.daily_summary,
        parameters={}
    )
    # Should not raise
    validate_report_definition(data)

def test_validate_empty_name():
    data = ReportDefinitionCreate(
        name="   ",
        report_type=ReportType.daily_summary,
        parameters={}
    )
    with pytest.raises(ValidationError, match="Report name must not be empty"):
        validate_report_definition(data)

def test_validate_scheduled_missing_cron():
    data = ReportDefinitionCreate(
        name="Scheduled",
        report_type=ReportType.daily_summary,
        is_scheduled=True,
        schedule_cron=""
    )
    with pytest.raises(ValidationError, match="Schedule cron is required"):
        validate_report_definition(data)

def test_validate_scheduled_invalid_cron():
    data = ReportDefinitionCreate(
        name="Scheduled",
        report_type=ReportType.daily_summary,
        is_scheduled=True,
        schedule_cron="0 0 * *" # Only 4 parts
    )
    with pytest.raises(ValidationError, match="Invalid cron expression"):
        validate_report_definition(data)

def test_validate_comparison_missing_periods():
    data = ReportDefinitionCreate(
        name="Comp",
        report_type=ReportType.comparison,
        parameters={"period_a": "2024-01"}
        # missing period_b
    )
    with pytest.raises(ValidationError, match="requires 'period_a' and 'period_b'"):
        validate_report_definition(data)

def test_validate_by_customer_accepts_empty():
    data = ReportDefinitionCreate(
        name="By Cust",
        report_type=ReportType.by_customer,
        parameters={}
    )
    validate_report_definition(data)

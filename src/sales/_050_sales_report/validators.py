from shared.errors import ValidationError
from src.sales._050_sales_report.models import ReportType
from src.sales._050_sales_report.schemas import ReportDefinitionCreate

def validate_report_definition(data: ReportDefinitionCreate) -> None:
    """Validate report definition data."""
    if not data.name or not data.name.strip():
        raise ValidationError("Report name must not be empty.")

    if data.is_scheduled:
        if not data.schedule_cron or not data.schedule_cron.strip():
            raise ValidationError("Schedule cron is required when is_scheduled is True.")
        parts = data.schedule_cron.split()
        if len(parts) != 5:
            raise ValidationError("Invalid cron expression.")

    params = data.parameters

    if data.report_type == ReportType.comparison:
        if "period_a" not in params or "period_b" not in params:
            raise ValidationError("Comparison report requires 'period_a' and 'period_b' in parameters.")

    elif data.report_type == ReportType.by_customer:
        if "customer_code" not in params:
            # Requires customer_code or accepts empty (all customers)
            pass

    elif data.report_type == ReportType.by_product:
        if "product_code" not in params:
            # Requires product_code or accepts empty (all products)
            pass

    elif data.report_type == ReportType.by_region:
        if "region" not in params:
            # Requires region or accepts empty (all regions)
            pass

    elif data.report_type == ReportType.by_salesperson:
        if "employee_code" not in params:
            # Requires employee_code or accepts empty (all)
            pass

from typing import Any, Optional
from datetime import datetime, date
from pydantic import Field
from shared.types import BaseSchema
from src.sales._050_sales_report.models import ReportType

class ReportDefinitionCreate(BaseSchema):
    """Schema for creating a report definition."""
    name: str = Field(..., max_length=200)
    report_type: ReportType
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_scheduled: bool = False
    schedule_cron: Optional[str] = Field(None, max_length=50)

class ReportDefinitionResponse(ReportDefinitionCreate):
    """Schema for report definition response."""
    id: int
    created_by: str
    created_at: datetime
    updated_at: datetime

class ReportData(BaseSchema):
    """Schema for report execution result."""
    report_type: ReportType
    generated_at: datetime
    headers: list[str]
    rows: list[dict[str, Any]]
    summary: Optional[dict[str, Any]] = None

class ReportFilter(BaseSchema):
    """Schema for filtering report definitions."""
    report_type: Optional[ReportType] = None
    created_by: Optional[str] = None
    is_scheduled: Optional[bool] = None

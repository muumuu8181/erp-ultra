from datetime import datetime
from sqlalchemy import String, Boolean, JSON, DateTime, Integer, Enum as SQLAlchemyEnum, func
from sqlalchemy.orm import Mapped, mapped_column
import enum
from shared.types import Base

class ReportType(str, enum.Enum):
    """Types of sales reports."""
    daily_summary = "daily_summary"
    monthly_summary = "monthly_summary"
    by_customer = "by_customer"
    by_product = "by_product"
    by_region = "by_region"
    by_salesperson = "by_salesperson"
    comparison = "comparison"

class ReportDefinition(Base):
    """Model for sales report definition."""
    __tablename__ = "sales_report_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(SQLAlchemyEnum(ReportType), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    schedule_cron: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

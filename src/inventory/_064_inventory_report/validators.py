from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, ValidationError
from src.inventory._064_inventory_report.models import InventoryReport
from src.inventory._064_inventory_report.schemas import InventoryReportCreate, InventoryReportUpdate


async def validate_unique_code(db: AsyncSession, code: str, current_id: int | None = None) -> None:
    """Validate that the inventory report code is unique."""
    query = select(InventoryReport).where(InventoryReport.code == code)
    if current_id is not None:
        query = query.where(InventoryReport.id != current_id)

    result = await db.execute(query)
    if result.scalars().first() is not None:
        raise DuplicateError(resource="InventoryReport", key=f"code={code}")


def validate_report_type(report_type: str) -> None:
    """Validate that the report_type is a valid, supported type."""
    valid_types = {"stock_level", "inventory_valuation", "stock_movement", "aging_analysis"}
    if report_type not in valid_types:
        raise ValidationError(
            message=f"Invalid report type: '{report_type}'. Must be one of {valid_types}.",
            field="report_type"
        )


def validate_status(status: str) -> None:
    """Validate that the status is a recognized value."""
    valid_statuses = {"draft", "processing", "completed", "failed"}
    if status not in valid_statuses:
        raise ValidationError(
            message=f"Invalid status: '{status}'. Must be one of {valid_statuses}.",
            field="status"
        )


async def validate_inventory_report_create(db: AsyncSession, data: InventoryReportCreate) -> None:
    """Run all validations for creating an inventory report."""
    await validate_unique_code(db, data.code)
    validate_report_type(data.report_type)
    if data.status:
        validate_status(data.status)


async def validate_inventory_report_update(db: AsyncSession, report_id: int, data: InventoryReportUpdate) -> None:
    """Run all validations for updating an inventory report."""
    if data.code is not None:
        await validate_unique_code(db, data.code, current_id=report_id)
    if data.report_type is not None:
        validate_report_type(data.report_type)
    if data.status is not None:
        validate_status(data.status)

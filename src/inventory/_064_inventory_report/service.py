from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError
from src.inventory._064_inventory_report.models import InventoryReport
from src.inventory._064_inventory_report.schemas import InventoryReportCreate, InventoryReportUpdate
from src.inventory._064_inventory_report.validators import (
    validate_inventory_report_create,
    validate_inventory_report_update,
)


async def create_inventory_report(db: AsyncSession, data: InventoryReportCreate) -> InventoryReport:
    """Create a new inventory report."""
    await validate_inventory_report_create(db, data)

    report = InventoryReport(**data.model_dump())
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_inventory_report(db: AsyncSession, report_id: int) -> InventoryReport:
    """Retrieve an inventory report by ID."""
    report = await db.get(InventoryReport, report_id)
    if report is None:
        raise NotFoundError(resource="InventoryReport", resource_id=str(report_id))
    return report


async def list_inventory_reports(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[InventoryReport], int]:
    """List inventory reports with pagination."""
    # Count total
    count_query = select(func.count()).select_from(InventoryReport)
    total = await db.scalar(count_query) or 0

    # Get items
    query = select(InventoryReport).offset(skip).limit(limit).order_by(InventoryReport.id)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def update_inventory_report(db: AsyncSession, report_id: int, data: InventoryReportUpdate) -> InventoryReport:
    """Update an existing inventory report."""
    report = await get_inventory_report(db, report_id)

    await validate_inventory_report_update(db, report_id, data)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(report, key, value)

    await db.commit()
    await db.refresh(report)
    return report


async def delete_inventory_report(db: AsyncSession, report_id: int) -> None:
    """Delete an inventory report."""
    report = await get_inventory_report(db, report_id)
    await db.delete(report)
    await db.commit()

import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.types import PaginatedResponse
from src.foundation._001_database.engine import get_db
from src.inventory._064_inventory_report import service
from src.inventory._064_inventory_report.schemas import (
    InventoryReportCreate,
    InventoryReportResponse,
    InventoryReportUpdate,
)

router = APIRouter(prefix="/api/v1/inventory-reports", tags=["inventory-reports"])


@router.post("/", response_model=InventoryReportResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_report(
    data: InventoryReportCreate,
    db: AsyncSession = Depends(get_db)
) -> InventoryReportResponse:
    """Create a new inventory report."""
    report = await service.create_inventory_report(db, data)
    return InventoryReportResponse.model_validate(report)


@router.get("/{report_id}", response_model=InventoryReportResponse)
async def get_inventory_report(
    report_id: int,
    db: AsyncSession = Depends(get_db)
) -> InventoryReportResponse:
    """Retrieve an inventory report by its ID."""
    report = await service.get_inventory_report(db, report_id)
    return InventoryReportResponse.model_validate(report)


@router.get("/", response_model=PaginatedResponse[InventoryReportResponse])
async def list_inventory_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[InventoryReportResponse]:
    """List inventory reports with pagination."""
    skip = (page - 1) * page_size
    items, total = await service.list_inventory_reports(db, skip=skip, limit=page_size)

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse[InventoryReportResponse](
        items=[InventoryReportResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.put("/{report_id}", response_model=InventoryReportResponse)
async def update_inventory_report(
    report_id: int,
    data: InventoryReportUpdate,
    db: AsyncSession = Depends(get_db)
) -> InventoryReportResponse:
    """Update an existing inventory report."""
    report = await service.update_inventory_report(db, report_id, data)
    return InventoryReportResponse.model_validate(report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_report(
    report_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an inventory report."""
    await service.delete_inventory_report(db, report_id)

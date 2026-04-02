from fastapi import APIRouter, Depends, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import get_db
from datetime import date

from shared.types import PaginatedResponse
from src.inventory._057_warehouse_mgmt import service
from src.inventory._057_warehouse_mgmt.schemas import (
    OperationCreate,
    OperationUpdate,
    OperationResponse,
    PickListResponse,
    ProductivityResponse
)

router = APIRouter(prefix="/api/v1/warehouse-operations", tags=["Warehouse Operations"])


@router.post("", response_model=OperationResponse, status_code=status.HTTP_201_CREATED)
async def create_operation(
    data: OperationCreate, db: AsyncSession = Depends(get_db)
) -> OperationResponse:
    """Create a new warehouse operation."""
    op = await service.create_operation(db, data)
    return OperationResponse.model_validate(op)


@router.get("", response_model=PaginatedResponse[OperationResponse])
async def list_operations(
    warehouse_code: str | None = None,
    operation_type: str | None = None,
    op_status: str | None = Query(None, alias="status"),
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[OperationResponse]:
    """List operations with filters."""
    paginated = await service.list_operations(
        db,
        warehouse_code=warehouse_code,
        operation_type=operation_type,
        status=op_status,
        page=page,
        page_size=page_size
    )
    items = [OperationResponse.model_validate(item) for item in paginated.items]
    return PaginatedResponse(
        items=items,
        total=paginated.total,
        page=paginated.page,
        page_size=paginated.page_size,
        total_pages=paginated.total_pages
    )


@router.get("/productivity", response_model=ProductivityResponse)
async def get_productivity(
    warehouse_code: str,
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db)
) -> ProductivityResponse:
    """Get productivity metrics."""
    metrics = await service.get_productivity(db, warehouse_code, date_from, date_to)
    return ProductivityResponse(**metrics)


@router.post("/pick-list", response_model=PickListResponse)
async def generate_pick_list(
    warehouse_code: str = Body(embed=True),
    reference_type: str = Body(embed=True),
    reference_number: str = Body(embed=True),
    assigned_to: str = Body(embed=True),
    db: AsyncSession = Depends(get_db)
) -> PickListResponse:
    """Generate optimized pick list."""
    response = await service.generate_pick_list(db, warehouse_code, reference_type, reference_number, assigned_to)
    return response


@router.get("/{id}", response_model=OperationResponse)
async def get_operation(
    id: int, db: AsyncSession = Depends(get_db)
) -> OperationResponse:
    """Get a specific operation by ID."""
    op = await service.get_operation(db, id)
    return OperationResponse.model_validate(op)


@router.put("/{id}", response_model=OperationResponse)
async def update_operation(
    id: int, data: OperationUpdate, db: AsyncSession = Depends(get_db)
) -> OperationResponse:
    """Update a pending operation."""
    op = await service.update_operation(db, id, data)
    return OperationResponse.model_validate(op)


@router.post("/{id}/start", response_model=OperationResponse)
async def start_operation(
    id: int, db: AsyncSession = Depends(get_db)
) -> OperationResponse:
    """Start an operation."""
    op = await service.start_operation(db, id)
    return OperationResponse.model_validate(op)


@router.post("/{id}/tasks/{task_id}/complete", response_model=OperationResponse)
async def complete_task(
    id: int, task_id: int, db: AsyncSession = Depends(get_db)
) -> OperationResponse:
    """Complete a task."""
    await service.complete_task(db, id, task_id)
    op = await service.get_operation(db, id)
    return OperationResponse.model_validate(op)


@router.post("/{id}/complete", response_model=OperationResponse)
async def complete_operation(
    id: int, db: AsyncSession = Depends(get_db)
) -> OperationResponse:
    """Complete an operation."""
    op = await service.complete_operation(db, id)
    return OperationResponse.model_validate(op)


@router.post("/{id}/cancel", response_model=OperationResponse)
async def cancel_operation(
    id: int, reason: str | None = Body(None, embed=True), db: AsyncSession = Depends(get_db)
) -> OperationResponse:
    """Cancel an operation."""
    op = await service.cancel_operation(db, id, reason)
    return OperationResponse.model_validate(op)
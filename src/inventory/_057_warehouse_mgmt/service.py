from datetime import datetime, date, timezone
from decimal import Decimal
import math
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from shared.errors import NotFoundError, BusinessRuleError
from shared.types import PaginatedResponse
from src.inventory._057_warehouse_mgmt.models import (
    WarehouseOperation,
    OperationTask,
    OperationStatus,
    TaskStatus,
    OperationType,
    PriorityEnum
)
from src.inventory._057_warehouse_mgmt.schemas import (
    OperationCreate,
    OperationUpdate,
    PickListResponse,
    TaskResponse
)
from src.inventory._057_warehouse_mgmt.validators import (
    validate_create_operation,
    validate_status_transition,
    validate_can_cancel_operation,
    validate_can_update_operation,
    validate_all_tasks_completed
)


async def create_operation(db: AsyncSession, data: OperationCreate) -> WarehouseOperation:
    """Create a new warehouse operation with its tasks."""
    await validate_create_operation(db, data)

    op = WarehouseOperation(
        operation_number=data.operation_number,
        warehouse_code=data.warehouse_code,
        operation_type=data.operation_type,
        reference_type=data.reference_type,
        reference_number=data.reference_number,
        assigned_to=data.assigned_to,
        priority=data.priority or PriorityEnum.medium,
        notes=data.notes,
        created_by=data.created_by,
        status=OperationStatus.pending
    )

    db.add(op)
    await db.flush()

    for task_data in data.tasks:
        task = OperationTask(
            operation_id=op.id,
            task_number=task_data.task_number,
            product_code=task_data.product_code,
            product_name=task_data.product_name,
            quantity=task_data.quantity,
            from_bin=task_data.from_bin,
            to_bin=task_data.to_bin,
            status=TaskStatus.pending
        )
        db.add(task)

    await db.commit()
    await db.refresh(op)
    op = await get_operation(db, op.id)
    return op


async def start_operation(db: AsyncSession, operation_id: int) -> WarehouseOperation:
    """Start an operation, transition from pending to in_progress."""
    op = await get_operation(db, operation_id)

    validate_status_transition(op.status, OperationStatus.in_progress)

    op.status = OperationStatus.in_progress
    op.started_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(op)
    return op


async def complete_task(db: AsyncSession, operation_id: int, task_id: int) -> OperationTask:
    """Mark a task as completed and auto-complete the operation if all tasks are done."""
    op = await get_operation(db, operation_id)

    if op.status != OperationStatus.in_progress:
        raise BusinessRuleError("Can only complete tasks for in_progress operations")

    task = None
    for t in op.tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        raise NotFoundError("OperationTask", str(task_id))

    if task.status == TaskStatus.completed:
        return task

    task.status = TaskStatus.completed
    task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    all_completed = all(t.status == TaskStatus.completed for t in op.tasks)
    if all_completed:
        op.status = OperationStatus.completed
        op.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(task)
    return task


async def complete_operation(db: AsyncSession, operation_id: int) -> WarehouseOperation:
    """Complete an operation."""
    op = await get_operation(db, operation_id)

    validate_status_transition(op.status, OperationStatus.completed)
    validate_all_tasks_completed(op.tasks)

    op.status = OperationStatus.completed
    op.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(op)
    return op


async def cancel_operation(db: AsyncSession, operation_id: int, reason: str | None) -> WarehouseOperation:
    """Cancel a pending operation."""
    op = await get_operation(db, operation_id)

    validate_can_cancel_operation(op.status)
    validate_status_transition(op.status, OperationStatus.cancelled)

    op.status = OperationStatus.cancelled
    if reason:
        op.notes = (op.notes + f"\nCancelled: {reason}") if op.notes else f"Cancelled: {reason}"

    await db.commit()
    await db.refresh(op)
    return op


async def update_operation(db: AsyncSession, operation_id: int, data: OperationUpdate) -> WarehouseOperation:
    """Update a pending operation."""
    op = await get_operation(db, operation_id)

    validate_can_update_operation(op.status)

    if data.assigned_to is not None:
        op.assigned_to = data.assigned_to
    if data.priority is not None:
        op.priority = data.priority
    if data.notes is not None:
        op.notes = data.notes

    await db.commit()
    await db.refresh(op)
    return op


async def generate_pick_list(db: AsyncSession, warehouse_code: str, reference_type: str, reference_number: str, assigned_to: str) -> PickListResponse:
    """Create a pick operation with tasks sorted by bin location order."""
    stmt = (
        select(WarehouseOperation)
        .options(selectinload(WarehouseOperation.tasks))
        .where(
            and_(
                WarehouseOperation.warehouse_code == warehouse_code,
                WarehouseOperation.reference_type == reference_type,
                WarehouseOperation.reference_number == reference_number
            )
        )
    )
    result = await db.execute(stmt)
    existing_ops = result.scalars().all()

    if not existing_ops:
        op_number = f"PICK-{uuid.uuid4().hex[:8].upper()}"
        op = WarehouseOperation(
            operation_number=op_number,
            warehouse_code=warehouse_code,
            operation_type=OperationType.pick,
            reference_type=reference_type,
            reference_number=reference_number,
            assigned_to=assigned_to,
            priority=PriorityEnum.medium,
            created_by="system",
            status=OperationStatus.pending
        )
        db.add(op)
        await db.commit()
        op = await get_operation(db, op.id)
    else:
        op = existing_ops[0]

    sorted_tasks = sorted(op.tasks, key=lambda t: t.from_bin or "")

    total_items = len(sorted_tasks)
    total_quantity = sum(t.quantity for t in sorted_tasks)

    return PickListResponse(
        operation_id=op.id,
        operation_number=op.operation_number,
        warehouse_code=op.warehouse_code,
        tasks=[TaskResponse.model_validate(t) for t in sorted_tasks],
        total_items=total_items,
        total_quantity=total_quantity
    )


async def get_operation(db: AsyncSession, operation_id: int) -> WarehouseOperation:
    """Fetch an operation by ID with its tasks."""
    stmt = (
        select(WarehouseOperation)
        .options(selectinload(WarehouseOperation.tasks))
        .where(WarehouseOperation.id == operation_id)
    )
    result = await db.execute(stmt)
    op = result.scalar_one_or_none()

    if not op:
        raise NotFoundError("WarehouseOperation", str(operation_id))

    return op


async def list_operations(
    db: AsyncSession,
    warehouse_code: str | None = None,
    operation_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50
) -> PaginatedResponse:
    """List operations with pagination and filters."""
    conditions = []
    if warehouse_code:
        conditions.append(WarehouseOperation.warehouse_code == warehouse_code)
    if operation_type:
        conditions.append(WarehouseOperation.operation_type == operation_type)
    if status:
        conditions.append(WarehouseOperation.status == status)

    stmt = select(WarehouseOperation).options(selectinload(WarehouseOperation.tasks))
    if conditions:
        stmt = stmt.where(and_(*conditions))

    count_stmt = select(func.count()).select_from(WarehouseOperation)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def get_productivity(db: AsyncSession, warehouse_code: str, date_from: date, date_to: date) -> dict:
    """Calculate productivity metrics."""
    dt_from = datetime.combine(date_from, datetime.min.time())
    dt_to = datetime.combine(date_to, datetime.max.time())

    stmt = select(WarehouseOperation).where(
        and_(
            WarehouseOperation.warehouse_code == warehouse_code,
            WarehouseOperation.created_at >= dt_from,
            WarehouseOperation.created_at <= dt_to
        )
    )
    result = await db.execute(stmt)
    ops = result.scalars().all()

    total_operations = len(ops)
    completed_ops = [op for op in ops if op.status == OperationStatus.completed]
    completed_count = len(completed_ops)

    hours_in_range = (dt_to - dt_from).total_seconds() / 3600
    if hours_in_range <= 0:
        hours_in_range = 24

    operations_per_hour = completed_count / hours_in_range if hours_in_range > 0 else 0
    completion_rate = (completed_count / total_operations * 100) if total_operations > 0 else 0

    total_minutes = 0
    valid_completed_ops = 0
    for op in completed_ops:
        if op.started_at and op.completed_at:
            mins = (op.completed_at - op.started_at).total_seconds() / 60
            total_minutes += mins
            valid_completed_ops += 1

    avg_completion_time = total_minutes / valid_completed_ops if valid_completed_ops > 0 else 0

    return {
        "operations_per_hour": operations_per_hour,
        "completion_rate": completion_rate,
        "total_operations": total_operations,
        "completed_operations": completed_count,
        "avg_completion_time_minutes": avg_completion_time
    }

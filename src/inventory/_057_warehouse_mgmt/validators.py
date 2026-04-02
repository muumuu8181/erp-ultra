from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.errors import ValidationError, BusinessRuleError, DuplicateError
from src.inventory._057_warehouse_mgmt.models import (
    OperationType,
    OperationStatus,
    TaskStatus,
    WarehouseOperation,
)
from src.inventory._057_warehouse_mgmt.schemas import OperationCreate


def validate_operation_type(op_type: str) -> None:
    """Validates the operation type."""
    try:
        OperationType(op_type)
    except ValueError:
        raise ValidationError(f"Invalid operation type: {op_type}", field="operation_type")


def validate_move_operation_bins(op_type: OperationType, from_bin: str | None, to_bin: str | None) -> None:
    """Validates that from_bin and to_bin are different for move operations."""
    if op_type in (OperationType.put_away, OperationType.replenish):
        if from_bin and to_bin and from_bin == to_bin:
            raise ValidationError("from_bin must not equal to_bin for move operations")


def validate_task_quantity(quantity: Decimal) -> None:
    """Validates that task quantity is greater than 0."""
    if quantity <= 0:
        raise ValidationError("Quantity must be > 0 on all tasks", field="quantity")


async def validate_operation_number_uniqueness(db: AsyncSession, operation_number: str) -> None:
    """Validates that the operation number is unique."""
    stmt = select(WarehouseOperation).where(WarehouseOperation.operation_number == operation_number)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise DuplicateError("WarehouseOperation", key=operation_number)


def validate_status_transition(current_status: OperationStatus, new_status: OperationStatus) -> None:
    """Validates allowed status transitions."""
    valid_transitions = {
        OperationStatus.pending: {OperationStatus.in_progress, OperationStatus.cancelled},
        OperationStatus.in_progress: {OperationStatus.completed},
        OperationStatus.completed: set(),
        OperationStatus.cancelled: set(),
    }

    if new_status not in valid_transitions.get(current_status, set()):
        raise BusinessRuleError(f"Invalid status transition from {current_status} to {new_status}")


def validate_all_tasks_completed(tasks: list) -> None:
    """Validates that all tasks are completed before completing the operation."""
    for task in tasks:
        if task.status != TaskStatus.completed:
            raise BusinessRuleError("All tasks must be completed before completing the operation")


def validate_can_update_operation(status: OperationStatus) -> None:
    """Validates that only pending operations can be updated."""
    if status != OperationStatus.pending:
        raise BusinessRuleError("Can only update operations in 'pending' status")


def validate_can_cancel_operation(status: OperationStatus) -> None:
    """Validates that only pending operations can be cancelled."""
    if status != OperationStatus.pending:
        raise BusinessRuleError("Can only cancel operations in 'pending' status")


async def validate_create_operation(db: AsyncSession, data: OperationCreate) -> None:
    """Combines all validation rules for creating an operation."""
    validate_operation_type(data.operation_type.value)
    await validate_operation_number_uniqueness(db, data.operation_number)

    for task in data.tasks:
        validate_task_quantity(task.quantity)
        validate_move_operation_bins(data.operation_type, task.from_bin, task.to_bin)
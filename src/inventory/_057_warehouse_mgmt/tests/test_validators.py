import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from shared.errors import ValidationError, BusinessRuleError, DuplicateError
from src.inventory._057_warehouse_mgmt.models import OperationType, OperationStatus, TaskStatus
from src.inventory._057_warehouse_mgmt.schemas import OperationCreate, TaskCreate
from src.inventory._057_warehouse_mgmt.validators import (
    validate_operation_type,
    validate_move_operation_bins,
    validate_task_quantity,
    validate_operation_number_uniqueness,
    validate_status_transition,
    validate_all_tasks_completed,
    validate_can_update_operation,
    validate_can_cancel_operation
)

pytestmark = pytest.mark.asyncio


def test_validate_operation_type():
    # Valid
    validate_operation_type("pick")

    # Invalid
    with pytest.raises(ValidationError):
        validate_operation_type("invalid_type")


def test_validate_move_operation_bins():
    # Put away with same bins
    with pytest.raises(ValidationError):
        validate_move_operation_bins(OperationType.put_away, "BIN-1", "BIN-1")

    # Replenish with same bins
    with pytest.raises(ValidationError):
        validate_move_operation_bins(OperationType.replenish, "BIN-1", "BIN-1")

    # Valid
    validate_move_operation_bins(OperationType.put_away, "BIN-1", "BIN-2")
    validate_move_operation_bins(OperationType.pick, "BIN-1", "BIN-1") # pick allows same bins theoretically or doesn't check it


def test_validate_task_quantity():
    with pytest.raises(ValidationError):
        validate_task_quantity(Decimal("0"))

    with pytest.raises(ValidationError):
        validate_task_quantity(Decimal("-1"))

    validate_task_quantity(Decimal("1"))


async def test_validate_operation_number_uniqueness():
    mock_db = AsyncMock()
    # Mock finding an existing op
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "existing_op"
    mock_db.execute.return_value = mock_result

    with pytest.raises(DuplicateError):
        await validate_operation_number_uniqueness(mock_db, "OP-1")

    # Mock not finding
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    await validate_operation_number_uniqueness(mock_db, "OP-2")


def test_validate_status_transition():
    # Valid
    validate_status_transition(OperationStatus.pending, OperationStatus.in_progress)
    validate_status_transition(OperationStatus.pending, OperationStatus.cancelled)
    validate_status_transition(OperationStatus.in_progress, OperationStatus.completed)

    # Invalid
    with pytest.raises(BusinessRuleError):
        validate_status_transition(OperationStatus.pending, OperationStatus.completed)
    with pytest.raises(BusinessRuleError):
        validate_status_transition(OperationStatus.in_progress, OperationStatus.cancelled)


def test_validate_all_tasks_completed():
    class DummyTask:
        def __init__(self, status):
            self.status = status

    tasks_incomplete = [DummyTask(TaskStatus.completed), DummyTask(TaskStatus.pending)]
    with pytest.raises(BusinessRuleError):
        validate_all_tasks_completed(tasks_incomplete)

    tasks_complete = [DummyTask(TaskStatus.completed), DummyTask(TaskStatus.completed)]
    validate_all_tasks_completed(tasks_complete)


def test_validate_can_update_operation():
    validate_can_update_operation(OperationStatus.pending)

    with pytest.raises(BusinessRuleError):
        validate_can_update_operation(OperationStatus.in_progress)


def test_validate_can_cancel_operation():
    validate_can_cancel_operation(OperationStatus.pending)

    with pytest.raises(BusinessRuleError):
        validate_can_cancel_operation(OperationStatus.in_progress)

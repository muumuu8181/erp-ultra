import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import engine, async_session_factory
from shared.types import Base
from shared.errors import BusinessRuleError

from src.inventory._057_warehouse_mgmt.models import (
    OperationType,
    OperationStatus,
    TaskStatus,
    PriorityEnum
)
from src.inventory._057_warehouse_mgmt.schemas import OperationCreate, TaskCreate
from src.inventory._057_warehouse_mgmt import service

pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

async def test_create_operation(db):
    data = OperationCreate(
        operation_number="OP-SVC-1",
        warehouse_code="WH-1",
        operation_type=OperationType.pick,
        reference_type="so",
        reference_number="SO-1",
        assigned_to="user1",
        priority=PriorityEnum.high,
        created_by="system",
        tasks=[
            TaskCreate(
                task_number=1,
                product_code="PRD-1",
                product_name="Product 1",
                quantity=Decimal("10"),
                from_bin="A1",
                to_bin="B1"
            )
        ]
    )

    op = await service.create_operation(db, data)
    assert op.id is not None
    assert op.operation_number == "OP-SVC-1"
    assert op.status == OperationStatus.pending
    assert len(op.tasks) == 1
    assert op.tasks[0].status == TaskStatus.pending

async def test_start_operation(db):
    # Setup
    data = OperationCreate(
        operation_number="OP-SVC-2",
        warehouse_code="WH-1",
        operation_type=OperationType.put_away,
        reference_type="po",
        reference_number="PO-1",
        assigned_to="user1",
        created_by="system",
        tasks=[
            TaskCreate(
                task_number=1,
                product_code="PRD-1",
                product_name="Product 1",
                quantity=Decimal("10"),
                from_bin="RECV",
                to_bin="A1"
            )
        ]
    )
    op = await service.create_operation(db, data)

    # Start
    op_started = await service.start_operation(db, op.id)
    assert op_started.status == OperationStatus.in_progress
    assert op_started.started_at is not None

async def test_complete_task_and_auto_complete_operation(db):
    # Setup
    data = OperationCreate(
        operation_number="OP-SVC-3",
        warehouse_code="WH-1",
        operation_type=OperationType.pick,
        reference_type="so",
        reference_number="SO-2",
        assigned_to="user1",
        created_by="system",
        tasks=[
            TaskCreate(
                task_number=1,
                product_code="PRD-1",
                product_name="Product 1",
                quantity=Decimal("5"),
                from_bin="A1"
            )
        ]
    )
    op = await service.create_operation(db, data)
    op = await service.start_operation(db, op.id)

    op = await service.get_operation(db, op.id)
    task_id = op.tasks[0].id

    # Complete Task
    task = await service.complete_task(db, op.id, task_id)
    assert task.status == TaskStatus.completed
    assert task.completed_at is not None

    # Check auto-complete
    op_completed = await service.get_operation(db, op.id)
    assert op_completed.status == OperationStatus.completed
    assert op_completed.completed_at is not None

async def test_complete_operation_with_incomplete_tasks(db):
    data = OperationCreate(
        operation_number="OP-SVC-4",
        warehouse_code="WH-1",
        operation_type=OperationType.pick,
        reference_type="so",
        reference_number="SO-3",
        assigned_to="user1",
        created_by="system",
        tasks=[
            TaskCreate(
                task_number=1,
                product_code="PRD-1",
                product_name="Product 1",
                quantity=Decimal("5"),
                from_bin="A1"
            )
        ]
    )
    op = await service.create_operation(db, data)
    op = await service.start_operation(db, op.id)

    # Try complete without completing tasks
    with pytest.raises(BusinessRuleError, match="All tasks must be completed before completing the operation"):
        await service.complete_operation(db, op.id)

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.inventory._057_warehouse_mgmt.models import (
    WarehouseOperation,
    OperationTask,
    OperationType,
    OperationStatus,
    TaskStatus,
    PriorityEnum
)
from src.foundation._001_database.engine import engine, async_session_factory
from shared.types import Base

@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

pytestmark = pytest.mark.asyncio

async def test_warehouse_operation_creation(db_session):
    op = WarehouseOperation(
        operation_number="OP-123",
        warehouse_code="WH-1",
        operation_type=OperationType.put_away,
        reference_type="po",
        reference_number="PO-123",
        assigned_to="user1",
        priority=PriorityEnum.high,
        notes="Test note",
        created_by="system"
    )
    db_session.add(op)
    await db_session.commit()
    await db_session.refresh(op)

    assert op.id is not None
    assert op.operation_number == "OP-123"
    assert op.status == OperationStatus.pending
    assert op.priority == PriorityEnum.high

async def test_operation_task_creation(db_session):
    op = WarehouseOperation(
        operation_number="OP-124",
        warehouse_code="WH-1",
        operation_type=OperationType.pick,
        reference_type="so",
        reference_number="SO-124",
        assigned_to="user2",
        created_by="system"
    )
    db_session.add(op)
    await db_session.flush()

    task = OperationTask(
        operation_id=op.id,
        task_number=1,
        product_code="PRD-1",
        product_name="Product 1",
        quantity=Decimal("10.5"),
        from_bin="A1",
        to_bin="B1"
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.id is not None
    assert task.operation_id == op.id
    assert task.status == TaskStatus.pending
    assert task.quantity == Decimal("10.5")

async def test_unique_operation_number(db_session):
    op1 = WarehouseOperation(
        operation_number="OP-UNIQUE",
        warehouse_code="WH-1",
        operation_type=OperationType.pick,
        reference_type="so",
        reference_number="SO-1",
        assigned_to="user1",
        created_by="system"
    )
    db_session.add(op1)
    await db_session.commit()

    op2 = WarehouseOperation(
        operation_number="OP-UNIQUE",
        warehouse_code="WH-1",
        operation_type=OperationType.pick,
        reference_type="so",
        reference_number="SO-2",
        assigned_to="user1",
        created_by="system"
    )
    db_session.add(op2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

def test_operation_type_enum():
    assert OperationType.put_away.value == "put_away"
    assert OperationType.pick.value == "pick"
    assert OperationType.pack.value == "pack"
    assert OperationType.ship.value == "ship"
    assert OperationType.replenish.value == "replenish"

def test_status_enum():
    assert OperationStatus.pending.value == "pending"
    assert OperationStatus.in_progress.value == "in_progress"
    assert OperationStatus.completed.value == "completed"
    assert OperationStatus.cancelled.value == "cancelled"

def test_priority_enum():
    assert PriorityEnum.low.value == "low"
    assert PriorityEnum.medium.value == "medium"
    assert PriorityEnum.high.value == "high"
    assert PriorityEnum.urgent.value == "urgent"
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import engine, async_session_factory
from shared.types import Base
from shared.errors import BusinessRuleError, NotFoundError

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

async def test_cancel_operation(db):
    data = OperationCreate(
        operation_number="OP-SVC-CANCEL",
        warehouse_code="WH-1",
        operation_type=OperationType.put_away,
        reference_type="po",
        reference_number="PO-1",
        assigned_to="user1",
        created_by="system",
        tasks=[
            TaskCreate(task_number=1, product_code="P1", product_name="P1", quantity=Decimal("1"), from_bin="A", to_bin="B")
        ]
    )
    op = await service.create_operation(db, data)

    op_cancelled = await service.cancel_operation(db, op.id, reason="No stock")
    assert op_cancelled.status == OperationStatus.cancelled
    assert "No stock" in op_cancelled.notes

async def test_cancel_in_progress_operation_fails(db):
    data = OperationCreate(
        operation_number="OP-SVC-CANCEL-FAIL",
        warehouse_code="WH-1",
        operation_type=OperationType.put_away,
        reference_type="po",
        reference_number="PO-1",
        assigned_to="user1",
        created_by="system",
        tasks=[
            TaskCreate(task_number=1, product_code="P1", product_name="P1", quantity=Decimal("1"), from_bin="A", to_bin="B")
        ]
    )
    op = await service.create_operation(db, data)
    await service.start_operation(db, op.id)

    with pytest.raises(BusinessRuleError, match="Can only cancel operations in 'pending' status"):
        await service.cancel_operation(db, op.id, reason="Oops")

async def test_generate_pick_list(db):
    # Setup pending pick op for a specific ref
    data = OperationCreate(
        operation_number="OP-PICK-GEN",
        warehouse_code="WH-PICK",
        operation_type=OperationType.pick,
        reference_type="so",
        reference_number="SO-PICK-1",
        assigned_to="picker1",
        created_by="system",
        tasks=[
            TaskCreate(task_number=1, product_code="P1", product_name="P1", quantity=Decimal("1"), from_bin="Z-Bin"),
            TaskCreate(task_number=2, product_code="P2", product_name="P2", quantity=Decimal("2"), from_bin="A-Bin"),
            TaskCreate(task_number=3, product_code="P3", product_name="P3", quantity=Decimal("3"), from_bin="M-Bin"),
        ]
    )
    await service.create_operation(db, data)

    res = await service.generate_pick_list(
        db, warehouse_code="WH-PICK", reference_type="so", reference_number="SO-PICK-1", assigned_to="picker1"
    )
    assert res.total_items == 3
    assert res.total_quantity == Decimal("6")
    # check order
    assert res.tasks[0].from_bin == "A-Bin"
    assert res.tasks[1].from_bin == "M-Bin"
    assert res.tasks[2].from_bin == "Z-Bin"

async def test_get_operation_not_found(db):
    with pytest.raises(NotFoundError):
        await service.get_operation(db, 999999)

async def test_list_operations(db):
    data = OperationCreate(
        operation_number="OP-LIST-1",
        warehouse_code="WH-LIST",
        operation_type=OperationType.pack,
        reference_type="so",
        reference_number="SO-1",
        assigned_to="user1",
        created_by="sys",
        tasks=[]
    )
    await service.create_operation(db, data)

    res = await service.list_operations(db, warehouse_code="WH-LIST")
    assert res.total >= 1
    assert any(op.operation_number == "OP-LIST-1" for op in res.items)

    res_type = await service.list_operations(db, operation_type="pack")
    assert any(op.operation_number == "OP-LIST-1" for op in res_type.items)

    res_status = await service.list_operations(db, status=OperationStatus.pending)
    assert any(op.operation_number == "OP-LIST-1" for op in res_status.items)

async def test_get_productivity(db):
    # This just ensures the function runs and returns the expected structure
    # Metrics logic works via sql
    res = await service.get_productivity(db, warehouse_code="WH-1", date_from=date.today(), date_to=date.today())
    assert "operations_per_hour" in res
    assert "completion_rate" in res
    assert "total_operations" in res
    assert "completed_operations" in res
    assert "avg_completion_time_minutes" in res

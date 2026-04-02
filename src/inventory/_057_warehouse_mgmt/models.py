import enum
from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, String, Text, DateTime, Numeric, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.types import BaseModel


class OperationType(str, enum.Enum):
    put_away = "put_away"
    pick = "pick"
    pack = "pack"
    ship = "ship"
    replenish = "replenish"


class OperationStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class PriorityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class WarehouseOperation(BaseModel):
    __tablename__ = "warehouse_operation"

    operation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    warehouse_code: Mapped[str] = mapped_column(String(50), nullable=False)
    operation_type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[OperationStatus] = mapped_column(Enum(OperationStatus), nullable=False, default=OperationStatus.pending)
    assigned_to: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[PriorityEnum] = mapped_column(Enum(PriorityEnum), nullable=False, default=PriorityEnum.medium)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    tasks: Mapped[list["OperationTask"]] = relationship(
        "OperationTask", back_populates="operation", cascade="all, delete-orphan"
    )


class OperationTask(BaseModel):
    __tablename__ = "operation_task"

    operation_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouse_operation.id"), nullable=False)
    task_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    from_bin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_bin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.pending)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    operation: Mapped["WarehouseOperation"] = relationship(
        "WarehouseOperation", back_populates="tasks"
    )
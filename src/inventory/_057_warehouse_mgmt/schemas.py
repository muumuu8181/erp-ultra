from typing import Optional
from datetime import datetime
from decimal import Decimal
from shared.types import BaseSchema
from src.inventory._057_warehouse_mgmt.models import OperationType, OperationStatus, TaskStatus, PriorityEnum


class TaskCreate(BaseSchema):
    task_number: int
    product_code: str
    product_name: str
    quantity: Decimal
    from_bin: Optional[str] = None
    to_bin: Optional[str] = None


class TaskResponse(BaseSchema):
    id: int
    operation_id: int
    task_number: int
    product_code: str
    product_name: str
    quantity: Decimal
    from_bin: Optional[str]
    to_bin: Optional[str]
    status: TaskStatus
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class OperationCreate(BaseSchema):
    operation_number: str
    warehouse_code: str
    operation_type: OperationType
    reference_type: str
    reference_number: str
    assigned_to: str
    priority: Optional[PriorityEnum] = PriorityEnum.medium
    notes: Optional[str] = None
    created_by: str
    tasks: list[TaskCreate]


class OperationUpdate(BaseSchema):
    assigned_to: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    notes: Optional[str] = None


class OperationResponse(BaseSchema):
    id: int
    operation_number: str
    warehouse_code: str
    operation_type: OperationType
    reference_type: str
    reference_number: str
    status: OperationStatus
    assigned_to: str
    priority: PriorityEnum
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    tasks: list[TaskResponse]


class PickListResponse(BaseSchema):
    operation_id: int
    operation_number: str
    warehouse_code: str
    tasks: list[TaskResponse]
    total_items: int
    total_quantity: Decimal


class ProductivityResponse(BaseSchema):
    operations_per_hour: float
    completion_rate: float
    total_operations: int
    completed_operations: int
    avg_completion_time_minutes: float

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel as PydanticBaseModel, Field
from shared.types import BaseSchema
import enum


class TraceDirection(str, enum.Enum):
    forward = "forward"
    backward = "backward"


class SerialCreate(BaseSchema):
    serial_number: str = Field(..., max_length=100)
    product_code: str = Field(..., max_length=50)
    warehouse_code: str = Field(..., max_length=50)
    bin_code: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    supplier_code: Optional[str] = Field(None, max_length=50)
    customer_code: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[date] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    notes: Optional[str] = None


class SerialResponse(BaseSchema):
    id: int
    serial_number: str
    product_code: str
    warehouse_code: str
    bin_code: Optional[str] = None
    status: str
    supplier_code: Optional[str] = None
    customer_code: Optional[str] = None
    purchase_date: Optional[date] = None
    sale_date: Optional[date] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SerialHistoryResponse(BaseSchema):
    id: int
    serial_id: int
    event_type: str
    reference_type: str
    reference_number: str
    location_from: Optional[str] = None
    location_to: Optional[str] = None
    event_date: datetime
    notes: Optional[str] = None
    created_at: datetime


class SerialTraceRequest(BaseSchema):
    serial_number: str
    direction: TraceDirection


class SerialTraceResponse(BaseSchema):
    serial_number: str
    product_code: str
    current_status: str
    history: List[SerialHistoryResponse]


class WarrantyCheck(BaseSchema):
    serial_number: str
    check_date: date


class WarrantyCheckResponse(BaseSchema):
    serial_number: str
    product_code: str
    is_under_warranty: bool
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    days_remaining: Optional[int] = None

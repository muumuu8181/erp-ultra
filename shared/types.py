"""
Shared type definitions for all ERP modules.
Every module MUST use these types for cross-module consistency.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel as PydanticBase
from enum import Enum


T = TypeVar('T')


class BaseSchema(PydanticBase):
    """Base for all Pydantic schemas in the system."""
    class Config:
        from_attributes = True


class AuditableMixin(BaseSchema):
    """Mixin for entities that track creation/modification."""
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str


class SoftDeleteMixin(BaseSchema):
    """Mixin for soft-deletable entities."""
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


class PaginatedResponse(BaseSchema, Generic[T]):
    """Standard paginated response wrapper."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class Money(BaseSchema):
    """Monetary amount with currency."""
    amount: Decimal
    currency: str = "JPY"


class Address(BaseSchema):
    """Japanese address format."""
    postal_code: str
    prefecture: str
    city: str
    street: str
    building: Optional[str] = None


class ContactInfo(BaseSchema):
    """Contact information."""
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    mobile: Optional[str] = None


class DocumentStatus(str, Enum):
    """Standard document lifecycle status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    VOID = "void"


class TaxType(str, Enum):
    """Japanese tax classification."""
    STANDARD_10 = "standard_10"
    REDUCED_8 = "reduced_8"
    EXEMPT = "exempt"
    NON_TAXABLE = "non_taxable"


class PaymentStatus(str, Enum):
    """Payment lifecycle status."""
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    REFUNDED = "refunded"


class Priority(str, Enum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Quantity(BaseSchema):
    """Quantity with unit of measure."""
    value: Decimal
    unit: str


class DateRange(BaseSchema):
    """Date range filter."""
    start_date: date
    end_date: date


class CodeGenerator:
    """Standard document number generator pattern."""
    _counters: dict[str, int] = {}

    @classmethod
    def generate(cls, prefix: str, date_value: date | None = None) -> str:
        d = date_value or date.today()
        key = f"{prefix}-{d.strftime('%Y%m')}"
        cls._counters[key] = cls._counters.get(key, 0) + 1
        seq = cls._counters[key]
        return f"{prefix}-{d.strftime('%Y%m')}-{seq:04d}"

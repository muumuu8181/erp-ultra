"""
Pydantic schemas for Contract Management.
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from shared.types import BaseSchema, PaginatedResponse


class ContractStatus(str, Enum):
    """Lifecycle status of a contract."""
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ContractBase(BaseSchema):
    """Base fields for Contract."""
    customer_id: int
    start_date: date
    end_date: date
    status: ContractStatus = ContractStatus.DRAFT
    total_value: Decimal
    terms: Optional[str] = None


class ContractCreate(ContractBase):
    """Schema for creating a contract."""
    contract_number: str


class ContractUpdate(BaseSchema):
    """Schema for updating a contract. All fields optional."""
    customer_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ContractStatus] = None
    total_value: Optional[Decimal] = None
    terms: Optional[str] = None


class ContractRead(ContractBase):
    """Schema for returning a contract (includes IDs and timestamps)."""
    id: int
    contract_number: str

    # from SoftDeleteMixin
    is_deleted: bool


class PaginatedContractResponse(PaginatedResponse[ContractRead]):
    """Paginated list of contracts."""
    pass

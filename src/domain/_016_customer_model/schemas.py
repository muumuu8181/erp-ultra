from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import Field

from shared.types import BaseSchema


class CustomerContactCreate(BaseSchema):
    """Schema for adding a contact to a customer."""
    name: str
    department: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    is_primary: bool = False


class CustomerContactResponse(BaseSchema):
    """Schema for customer contact API responses."""
    id: int
    customer_id: int
    name: str
    department: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class CustomerCreate(BaseSchema):
    """Schema for creating a new customer."""
    code: str
    name: str
    name_kana: str | None = None
    type: Literal["corporate", "individual"]
    corporate_number: str | None = None
    postal_code: str | None = None
    prefecture: str | None = None
    city: str | None = None
    street: str | None = None
    building: str | None = None
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    fax: str | None = None
    payment_terms_id: int | None = None
    credit_limit: Decimal | None = None
    tax_type: Literal["standard_10", "reduced_8", "exempt", "non_taxable"]
    is_active: bool = True
    memo: str | None = None


class CustomerUpdate(BaseSchema):
    """Schema for updating an existing customer. All fields optional."""
    name: str | None = None
    name_kana: str | None = None
    type: Literal["corporate", "individual"] | None = None
    corporate_number: str | None = None
    postal_code: str | None = None
    prefecture: str | None = None
    city: str | None = None
    street: str | None = None
    building: str | None = None
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    fax: str | None = None
    payment_terms_id: int | None = None
    credit_limit: Decimal | None = None
    tax_type: Literal["standard_10", "reduced_8", "exempt", "non_taxable"] | None = None
    is_active: bool | None = None
    memo: str | None = None


class CustomerResponse(BaseSchema):
    """Schema for customer API responses."""
    id: int
    code: str
    name: str
    name_kana: str | None = None
    type: str
    corporate_number: str | None = None
    postal_code: str | None = None
    prefecture: str | None = None
    city: str | None = None
    street: str | None = None
    building: str | None = None
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    fax: str | None = None
    payment_terms_id: int | None = None
    credit_limit: Decimal | None = None
    tax_type: str
    is_active: bool
    memo: str | None = None
    contacts: list[CustomerContactResponse] = []
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseSchema):
    """Paginated customer list response."""
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int

from datetime import datetime
from typing import Optional
from pydantic import Field, EmailStr

from shared.types import BaseSchema

class ContactBase(BaseSchema):
    """Base schema for Contact."""
    first_name: str = Field(..., max_length=200)
    last_name: str = Field(..., max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=200)
    position: Optional[str] = Field(None, max_length=200)
    is_primary: bool = False
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    notes: Optional[str] = None

class ContactCreate(ContactBase):
    """Schema for creating a new Contact."""
    pass

class ContactUpdate(BaseSchema):
    """Schema for updating an existing Contact."""
    first_name: Optional[str] = Field(None, max_length=200)
    last_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=200)
    position: Optional[str] = Field(None, max_length=200)
    is_primary: Optional[bool] = None
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    notes: Optional[str] = None

class ContactResponse(ContactBase):
    """Schema for returning a Contact."""
    id: int
    created_at: datetime
    updated_at: datetime

"""
Pydantic schemas for Payment Terms module.
"""
from typing import Optional
from datetime import datetime

from pydantic import Field

from shared.types import BaseSchema


class PaymentTermCreate(BaseSchema):
    """Schema for creating a new Payment Term."""
    code: str = Field(..., max_length=50, description="Unique code for the payment term")
    name: str = Field(..., max_length=200, description="Name of the payment term")
    description: Optional[str] = Field(None, description="Detailed description")
    days: int = Field(0, ge=0, description="Number of days for payment")
    is_active: bool = Field(True, description="Whether the payment term is active")


class PaymentTermUpdate(BaseSchema):
    """Schema for updating an existing Payment Term."""
    code: Optional[str] = Field(None, max_length=50, description="Unique code for the payment term")
    name: Optional[str] = Field(None, max_length=200, description="Name of the payment term")
    description: Optional[str] = Field(None, description="Detailed description")
    days: Optional[int] = Field(None, ge=0, description="Number of days for payment")
    is_active: Optional[bool] = Field(None, description="Whether the payment term is active")


class PaymentTermResponse(BaseSchema):
    """Schema for Payment Term response."""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

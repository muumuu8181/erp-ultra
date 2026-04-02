"""
Pydantic schemas for Address Book module.
"""
from typing import Optional
from pydantic import Field
from shared.types import BaseSchema, Address as SharedAddressType
from datetime import datetime


class AddressCreate(BaseSchema):
    """Schema for creating a new address."""
    postal_code: str = Field(..., max_length=20, description="Postal code")
    prefecture: str = Field(..., max_length=50, description="Prefecture")
    city: str = Field(..., max_length=100, description="City")
    street: str = Field(..., max_length=200, description="Street address")
    building: Optional[str] = Field(None, max_length=200, description="Building name/number")


class AddressUpdate(BaseSchema):
    """Schema for updating an existing address."""
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    prefecture: Optional[str] = Field(None, max_length=50, description="Prefecture")
    city: Optional[str] = Field(None, max_length=100, description="City")
    street: Optional[str] = Field(None, max_length=200, description="Street address")
    building: Optional[str] = Field(None, max_length=200, description="Building name/number")


class AddressResponse(SharedAddressType):
    """Schema for returning address details."""
    id: int = Field(..., description="Unique identifier for the address")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}

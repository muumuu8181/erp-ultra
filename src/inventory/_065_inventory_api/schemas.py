from typing import Optional
from pydantic import Field
from shared.types import BaseSchema, AuditableMixin


class InventoryEndpointBase(BaseSchema):
    """Base schema for Inventory API endpoint."""
    name: str = Field(..., max_length=200, description="Name of the endpoint")
    path: str = Field(..., max_length=500, description="Path of the endpoint")
    method: str = Field(..., max_length=20, description="HTTP method (e.g., GET, POST)")
    description: Optional[str] = Field(None, description="Detailed description")
    is_active: bool = Field(True, description="Whether the endpoint is currently active")


class InventoryEndpointCreate(InventoryEndpointBase):
    """Schema for creating a new Inventory API endpoint."""
    pass


class InventoryEndpointUpdate(BaseSchema):
    """Schema for updating an existing Inventory API endpoint."""
    name: Optional[str] = Field(None, max_length=200, description="Name of the endpoint")
    path: Optional[str] = Field(None, max_length=500, description="Path of the endpoint")
    method: Optional[str] = Field(None, max_length=20, description="HTTP method")
    description: Optional[str] = Field(None, description="Detailed description")
    is_active: Optional[bool] = Field(None, description="Whether the endpoint is currently active")


class InventoryEndpointResponse(InventoryEndpointBase):
    """Schema for reading an Inventory API endpoint."""
    id: int

    class Config:
        from_attributes = True

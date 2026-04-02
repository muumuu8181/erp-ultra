"""
Pydantic Schemas for Document Number Generator.
"""
from typing import Optional

from pydantic import Field

from shared.types import BaseSchema


class DocumentSequenceBase(BaseSchema):
    """Base schema for document sequence."""
    prefix: str = Field(..., max_length=50, description="The unique prefix for the sequence (e.g., INV, PO).")
    pattern: str = Field(
        ...,
        max_length=100,
        description="The pattern for generating the number (e.g., {prefix}-{YYMM}-{seq:04d}).",
    )
    description: Optional[str] = Field(None, max_length=500, description="Optional description.")
    is_active: bool = Field(True, description="Whether this sequence is active.")


class DocumentSequenceCreate(DocumentSequenceBase):
    """Schema for creating a new document sequence."""
    current_sequence: int = Field(0, description="Initial sequence number. Usually 0.")


class DocumentSequenceUpdate(BaseSchema):
    """Schema for updating an existing document sequence."""
    pattern: Optional[str] = Field(None, max_length=100, description="New pattern.")
    description: Optional[str] = Field(None, max_length=500, description="New description.")
    is_active: Optional[bool] = Field(None, description="New active status.")


class DocumentSequenceResponse(DocumentSequenceBase):
    """Schema for response containing document sequence data."""
    id: int
    current_sequence: int


class GeneratedDocumentNumberResponse(BaseSchema):
    """Schema for the response of generating a new document number."""
    document_number: str = Field(..., description="The newly generated document number.")
    prefix: str = Field(..., description="The prefix used.")
    sequence: int = Field(..., description="The sequence number assigned.")

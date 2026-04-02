"""
Schemas for the error handler module.
"""

from shared.types import BaseSchema
from pydantic import Field
from datetime import datetime
from typing import Optional, Any


class ErrorResponse(BaseSchema):
    """Standard error response returned for all error types."""
    code: str = Field(..., description="Machine-readable error code (e.g. VALIDATION_ERROR)")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


class ErrorCodeInfo(BaseSchema):
    """Information about a single error code."""
    code: str = Field(..., description="Error code string")
    http_status: int = Field(..., description="HTTP status code mapped to this error")
    description: str = Field(..., description="Human-readable description of when this error occurs")
    example_message: str = Field(..., description="Example error message")


class ErrorCodesResponse(BaseSchema):
    """Response listing all error codes."""
    codes: list[ErrorCodeInfo] = Field(..., description="List of all error codes")
    total: int = Field(..., description="Total number of error codes")

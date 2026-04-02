from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import Field
from shared.types import BaseSchema

class LogEntryCreate(BaseSchema):
    """Schema for creating a new log entry."""
    level: str = Field(..., description="Log level (e.g., INFO, ERROR, DEBUG)")
    message: str = Field(..., description="Log message")
    module: str = Field(..., description="Module generating the log")
    trace_id: Optional[str] = Field(None, description="Trace ID for correlation")
    user_id: Optional[str] = Field(None, description="User ID associated with the log")
    metadata_: Optional[Dict[str, Any]] = Field(None, description="Additional context/metadata")

class LogEntryUpdate(BaseSchema):
    """Schema for updating a log entry (typically not used much for logs)."""
    level: Optional[str] = Field(None, description="Log level (e.g., INFO, ERROR, DEBUG)")
    message: Optional[str] = Field(None, description="Log message")
    module: Optional[str] = Field(None, description="Module generating the log")
    trace_id: Optional[str] = Field(None, description="Trace ID for correlation")
    user_id: Optional[str] = Field(None, description="User ID associated with the log")
    metadata_: Optional[Dict[str, Any]] = Field(None, description="Additional context/metadata")

class LogEntryResponse(BaseSchema):
    """Schema for a log entry response."""
    id: int
    level: str
    message: str
    module: str
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

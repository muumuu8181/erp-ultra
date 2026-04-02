from typing import Any, Optional
from datetime import datetime
from pydantic import Field
from shared.types import BaseSchema


class ValidationRuleBase(BaseSchema):
    """Base schema for validation rules."""
    name: str = Field(..., max_length=50, description="Unique name of the validation rule")
    description: Optional[str] = Field(None, max_length=200, description="Description of the rule")
    rule_type: str = Field(..., max_length=50, description="Type of the rule (e.g., regex, range)")
    parameters: Optional[dict[str, Any]] = Field(None, description="Rule specific parameters")
    error_message: str = Field(..., max_length=200, description="Error message to display when validation fails")
    is_active: bool = Field(True, description="Whether the rule is currently active")


class ValidationRuleCreate(ValidationRuleBase):
    """Schema for creating a new validation rule."""
    pass


class ValidationRuleUpdate(BaseSchema):
    """Schema for updating an existing validation rule."""
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    rule_type: Optional[str] = Field(None, max_length=50)
    parameters: Optional[dict[str, Any]] = Field(None)
    error_message: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = Field(None)


class ValidationRuleResponse(ValidationRuleBase):
    """Schema for a validation rule response, including DB fields."""
    id: int
    created_at: datetime
    updated_at: datetime


class ValidationRequest(BaseSchema):
    """Schema for requesting a validation check against a specific rule."""
    rule_name: str = Field(..., description="Name of the validation rule to evaluate against")
    value: Any = Field(..., description="Value to validate")


class ValidationResult(BaseSchema):
    """Schema for the result of a validation evaluation."""
    is_valid: bool = Field(..., description="True if validation passed, False otherwise")
    error_message: Optional[str] = Field(None, description="Error message if validation failed")

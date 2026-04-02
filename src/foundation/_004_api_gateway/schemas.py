"""
Pydantic schemas for API Gateway configuration.
Provides schemas for GatewayRoute and RateLimitRule operations.
"""
from datetime import datetime
from typing import Optional

from pydantic import Field

from shared.types import BaseSchema, PaginatedResponse


class GatewayRouteBase(BaseSchema):
    """Base schema for GatewayRoute."""
    path: str = Field(..., description="The path to match (e.g., /api/v1/users)", max_length=255)
    target_url: str = Field(..., description="The target URL to route to", max_length=512)
    is_active: bool = Field(default=True, description="Whether the route is active")


class GatewayRouteCreate(GatewayRouteBase):
    """Schema for creating a GatewayRoute."""
    pass


class GatewayRouteUpdate(BaseSchema):
    """Schema for updating a GatewayRoute."""
    path: Optional[str] = Field(None, description="The path to match", max_length=255)
    target_url: Optional[str] = Field(None, description="The target URL to route to", max_length=512)
    is_active: Optional[bool] = Field(None, description="Whether the route is active")


class GatewayRouteResponse(GatewayRouteBase):
    """Schema for a GatewayRoute response."""
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RateLimitRuleBase(BaseSchema):
    """Base schema for RateLimitRule."""
    path: str = Field(..., description="The path this rule applies to", max_length=255)
    client_id: Optional[str] = Field(None, description="Optional client ID this rule applies to", max_length=255)
    max_requests: int = Field(..., description="Maximum number of requests allowed in the time window", gt=0)
    window_seconds: int = Field(..., description="Time window in seconds", gt=0)
    is_active: bool = Field(default=True, description="Whether the rule is active")


class RateLimitRuleCreate(RateLimitRuleBase):
    """Schema for creating a RateLimitRule."""
    pass


class RateLimitRuleUpdate(BaseSchema):
    """Schema for updating a RateLimitRule."""
    path: Optional[str] = Field(None, description="The path this rule applies to", max_length=255)
    client_id: Optional[str] = Field(None, description="Optional client ID this rule applies to", max_length=255)
    max_requests: Optional[int] = Field(None, description="Maximum number of requests allowed in the time window", gt=0)
    window_seconds: Optional[int] = Field(None, description="Time window in seconds", gt=0)
    is_active: Optional[bool] = Field(None, description="Whether the rule is active")


class RateLimitRuleResponse(RateLimitRuleBase):
    """Schema for a RateLimitRule response."""
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


GatewayRoutePaginatedResponse = PaginatedResponse[GatewayRouteResponse]
RateLimitRulePaginatedResponse = PaginatedResponse[RateLimitRuleResponse]

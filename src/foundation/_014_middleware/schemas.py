from shared.types import BaseSchema
from pydantic import Field


class MiddlewareConfig(BaseSchema):
    """Configuration for all middleware components."""
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins. Use ['*'] for all in development."
    )
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed HTTP methods for CORS."
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed headers for CORS."
    )
    cors_allow_credentials: bool = Field(
        False,
        description="Whether to allow credentials in CORS requests."
    )
    timing_enabled: bool = Field(
        True,
        description="Whether RequestTimingMiddleware is active."
    )
    request_id_enabled: bool = Field(
        True,
        description="Whether RequestIdMiddleware is active."
    )
    request_id_header: str = Field(
        "X-Request-ID",
        description="Header name for request ID."
    )
    tenant_header_name: str = Field(
        "X-Tenant-ID",
        description="Header name for tenant ID extraction."
    )
    tenant_required: bool = Field(
        False,
        description="Whether tenant ID header is required."
    )


class MiddlewareStatusResponse(BaseSchema):
    """Response showing current middleware configuration."""
    middleware: list[str] = Field(..., description="List of active middleware names")
    config: MiddlewareConfig = Field(..., description="Current middleware configuration")

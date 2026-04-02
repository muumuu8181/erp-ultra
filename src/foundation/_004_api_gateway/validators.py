"""
Validation logic for API Gateway.
"""
from urllib.parse import urlparse

from shared.errors import ValidationError
from src.foundation._004_api_gateway.schemas import (
    GatewayRouteCreate,
    GatewayRouteUpdate,
    RateLimitRuleCreate,
    RateLimitRuleUpdate,
)


def validate_path(path: str) -> None:
    """Validate that a path starts with '/'."""
    if not path.startswith("/"):
        raise ValidationError("Path must start with '/'", field="path")


def validate_target_url(target_url: str) -> None:
    """Validate that the target URL is a valid absolute URL."""
    try:
        result = urlparse(target_url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError("Target URL must be an absolute URL with a scheme and domain", field="target_url")
        if result.scheme not in ("http", "https"):
            raise ValidationError("Target URL scheme must be http or https", field="target_url")
    except ValueError:
        raise ValidationError("Invalid target URL format", field="target_url")


def validate_gateway_route_create(data: GatewayRouteCreate) -> None:
    """Validate GatewayRoute creation data."""
    validate_path(data.path)
    validate_target_url(data.target_url)


def validate_gateway_route_update(data: GatewayRouteUpdate) -> None:
    """Validate GatewayRoute update data."""
    if data.path is not None:
        validate_path(data.path)
    if data.target_url is not None:
        validate_target_url(data.target_url)


def validate_rate_limit_rule_create(data: RateLimitRuleCreate) -> None:
    """Validate RateLimitRule creation data."""
    validate_path(data.path)
    if data.max_requests <= 0:
        raise ValidationError("max_requests must be greater than 0", field="max_requests")
    if data.window_seconds <= 0:
        raise ValidationError("window_seconds must be greater than 0", field="window_seconds")


def validate_rate_limit_rule_update(data: RateLimitRuleUpdate) -> None:
    """Validate RateLimitRule update data."""
    if data.path is not None:
        validate_path(data.path)
    if data.max_requests is not None and data.max_requests <= 0:
        raise ValidationError("max_requests must be greater than 0", field="max_requests")
    if data.window_seconds is not None and data.window_seconds <= 0:
        raise ValidationError("window_seconds must be greater than 0", field="window_seconds")

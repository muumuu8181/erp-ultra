import pytest
from pydantic import ValidationError
from src.foundation._004_api_gateway.schemas import GatewayRouteCreate, RateLimitRuleCreate


def test_gateway_route_create_schema_valid():
    schema = GatewayRouteCreate(
        path="/api/v1/test",
        target_url="http://localhost:8080"
    )
    assert schema.path == "/api/v1/test"
    assert schema.target_url == "http://localhost:8080"
    assert schema.is_active is True


def test_gateway_route_create_schema_path_too_long():
    with pytest.raises(ValidationError):
        GatewayRouteCreate(
            path="/" + "a" * 255,
            target_url="http://localhost:8080"
        )


def test_rate_limit_rule_create_schema_valid():
    schema = RateLimitRuleCreate(
        path="/api/v1/test",
        max_requests=100,
        window_seconds=60
    )
    assert schema.path == "/api/v1/test"
    assert schema.max_requests == 100
    assert schema.window_seconds == 60


def test_rate_limit_rule_create_schema_invalid_limits():
    with pytest.raises(ValidationError):
        RateLimitRuleCreate(
            path="/api/v1/test",
            max_requests=0,
            window_seconds=60
        )
    with pytest.raises(ValidationError):
        RateLimitRuleCreate(
            path="/api/v1/test",
            max_requests=100,
            window_seconds=0
        )

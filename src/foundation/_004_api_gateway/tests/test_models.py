import pytest
from src.foundation._004_api_gateway.models import GatewayRoute, RateLimitRule


def test_gateway_route_model():
    route = GatewayRoute(
        path="/api/v1/test",
        target_url="http://localhost:8080/test",
        is_active=True
    )
    assert route.path == "/api/v1/test"
    assert route.target_url == "http://localhost:8080/test"
    assert route.is_active is True


def test_rate_limit_rule_model():
    rule = RateLimitRule(
        path="/api/v1/test",
        client_id="client_1",
        max_requests=100,
        window_seconds=60,
        is_active=True
    )
    assert rule.path == "/api/v1/test"
    assert rule.client_id == "client_1"
    assert rule.max_requests == 100
    assert rule.window_seconds == 60
    assert rule.is_active is True

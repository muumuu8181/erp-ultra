"""
004_api_gateway - API Gateway and Rate Limiting Configuration.

Provides:
- GatewayRoute model and CRUD operations
- RateLimitRule model and CRUD operations
- REST API for managing routes and limits
"""
from src.foundation._004_api_gateway.models import GatewayRoute, RateLimitRule
from src.foundation._004_api_gateway.router import router
from src.foundation._004_api_gateway.schemas import (
    GatewayRouteCreate,
    GatewayRouteResponse,
    GatewayRouteUpdate,
    RateLimitRuleCreate,
    RateLimitRuleResponse,
    RateLimitRuleUpdate,
)

__all__ = [
    "GatewayRoute",
    "RateLimitRule",
    "GatewayRouteCreate",
    "GatewayRouteUpdate",
    "GatewayRouteResponse",
    "RateLimitRuleCreate",
    "RateLimitRuleUpdate",
    "RateLimitRuleResponse",
    "router",
]

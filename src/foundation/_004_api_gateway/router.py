"""
FastAPI router for API Gateway configuration.
Provides REST endpoints for GatewayRoute and RateLimitRule management.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database import get_db
from src.foundation._004_api_gateway import service
from src.foundation._004_api_gateway.schemas import (
    GatewayRouteCreate,
    GatewayRoutePaginatedResponse,
    GatewayRouteResponse,
    GatewayRouteUpdate,
    RateLimitRuleCreate,
    RateLimitRulePaginatedResponse,
    RateLimitRuleResponse,
    RateLimitRuleUpdate,
)

router = APIRouter(prefix="/api/v1/api-gateway", tags=["api-gateway"])

# --- Gateway Routes ---

@router.post(
    "/routes",
    response_model=GatewayRouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Gateway Route"
)
async def create_route(
    data: GatewayRouteCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new API Gateway Route configuration."""
    return await service.create_gateway_route(db, data)


@router.get(
    "/routes",
    response_model=GatewayRoutePaginatedResponse,
    summary="List Gateway Routes"
)
async def list_routes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all API Gateway Route configurations with pagination."""
    return await service.list_gateway_routes(db, page, page_size)


@router.get(
    "/routes/{route_id}",
    response_model=GatewayRouteResponse,
    summary="Get a Gateway Route"
)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a specific API Gateway Route configuration by ID."""
    return await service.get_gateway_route(db, route_id)


@router.put(
    "/routes/{route_id}",
    response_model=GatewayRouteResponse,
    summary="Update a Gateway Route"
)
async def update_route(
    route_id: int,
    data: GatewayRouteUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a specific API Gateway Route configuration."""
    return await service.update_gateway_route(db, route_id, data)


@router.delete(
    "/routes/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Gateway Route"
)
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a specific API Gateway Route configuration."""
    await service.delete_gateway_route(db, route_id)


# --- Rate Limit Rules ---

@router.post(
    "/rate-limits",
    response_model=RateLimitRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Rate Limit Rule"
)
async def create_rate_limit(
    data: RateLimitRuleCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new API Rate Limit Rule configuration."""
    return await service.create_rate_limit_rule(db, data)


@router.get(
    "/rate-limits",
    response_model=RateLimitRulePaginatedResponse,
    summary="List Rate Limit Rules"
)
async def list_rate_limits(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all API Rate Limit Rule configurations with pagination."""
    return await service.list_rate_limit_rules(db, page, page_size)


@router.get(
    "/rate-limits/{rule_id}",
    response_model=RateLimitRuleResponse,
    summary="Get a Rate Limit Rule"
)
async def get_rate_limit(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a specific API Rate Limit Rule configuration by ID."""
    return await service.get_rate_limit_rule(db, rule_id)


@router.put(
    "/rate-limits/{rule_id}",
    response_model=RateLimitRuleResponse,
    summary="Update a Rate Limit Rule"
)
async def update_rate_limit(
    rule_id: int,
    data: RateLimitRuleUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a specific API Rate Limit Rule configuration."""
    return await service.update_rate_limit_rule(db, rule_id, data)


@router.delete(
    "/rate-limits/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Rate Limit Rule"
)
async def delete_rate_limit(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a specific API Rate Limit Rule configuration."""
    await service.delete_rate_limit_rule(db, rule_id)

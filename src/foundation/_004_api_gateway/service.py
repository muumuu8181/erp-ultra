"""
Service logic for API Gateway configuration.
Provides CRUD operations for GatewayRoute and RateLimitRule.
"""
import math

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, NotFoundError
from src.foundation._004_api_gateway.models import GatewayRoute, RateLimitRule
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
from src.foundation._004_api_gateway.validators import (
    validate_gateway_route_create,
    validate_gateway_route_update,
    validate_rate_limit_rule_create,
    validate_rate_limit_rule_update,
)

# --- Gateway Route Services ---

async def create_gateway_route(db: AsyncSession, data: GatewayRouteCreate) -> GatewayRouteResponse:
    """Create a new GatewayRoute."""
    validate_gateway_route_create(data)

    route = GatewayRoute(**data.model_dump())
    db.add(route)

    try:
        await db.commit()
        await db.refresh(route)
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("GatewayRoute", data.path)

    return GatewayRouteResponse.model_validate(route)


async def get_gateway_route(db: AsyncSession, route_id: int) -> GatewayRouteResponse:
    """Get a GatewayRoute by ID."""
    result = await db.execute(select(GatewayRoute).where(GatewayRoute.id == route_id))
    route = result.scalar_one_or_none()

    if not route:
        raise NotFoundError("GatewayRoute", str(route_id))

    return GatewayRouteResponse.model_validate(route)


async def list_gateway_routes(db: AsyncSession, page: int = 1, page_size: int = 50) -> GatewayRoutePaginatedResponse:
    """List GatewayRoutes with pagination."""
    skip = (page - 1) * page_size

    # Get total count
    count_stmt = select(func.count()).select_from(GatewayRoute)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Get items
    stmt = select(GatewayRoute).offset(skip).limit(page_size).order_by(GatewayRoute.id)
    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return GatewayRoutePaginatedResponse(
        items=[GatewayRouteResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def update_gateway_route(db: AsyncSession, route_id: int, data: GatewayRouteUpdate) -> GatewayRouteResponse:
    """Update a GatewayRoute."""
    validate_gateway_route_update(data)

    result = await db.execute(select(GatewayRoute).where(GatewayRoute.id == route_id))
    route = result.scalar_one_or_none()

    if not route:
        raise NotFoundError("GatewayRoute", str(route_id))

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(route, key, value)

    try:
        await db.commit()
        await db.refresh(route)
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("GatewayRoute", str(data.path) if data.path else str(route_id))

    return GatewayRouteResponse.model_validate(route)


async def delete_gateway_route(db: AsyncSession, route_id: int) -> None:
    """Delete a GatewayRoute."""
    result = await db.execute(select(GatewayRoute).where(GatewayRoute.id == route_id))
    route = result.scalar_one_or_none()

    if not route:
        raise NotFoundError("GatewayRoute", str(route_id))

    await db.delete(route)
    await db.commit()


# --- Rate Limit Rule Services ---

async def create_rate_limit_rule(db: AsyncSession, data: RateLimitRuleCreate) -> RateLimitRuleResponse:
    """Create a new RateLimitRule."""
    validate_rate_limit_rule_create(data)

    rule = RateLimitRule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return RateLimitRuleResponse.model_validate(rule)


async def get_rate_limit_rule(db: AsyncSession, rule_id: int) -> RateLimitRuleResponse:
    """Get a RateLimitRule by ID."""
    result = await db.execute(select(RateLimitRule).where(RateLimitRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise NotFoundError("RateLimitRule", str(rule_id))

    return RateLimitRuleResponse.model_validate(rule)


async def list_rate_limit_rules(db: AsyncSession, page: int = 1, page_size: int = 50) -> RateLimitRulePaginatedResponse:
    """List RateLimitRules with pagination."""
    skip = (page - 1) * page_size

    count_stmt = select(func.count()).select_from(RateLimitRule)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = select(RateLimitRule).offset(skip).limit(page_size).order_by(RateLimitRule.id)
    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return RateLimitRulePaginatedResponse(
        items=[RateLimitRuleResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def update_rate_limit_rule(db: AsyncSession, rule_id: int, data: RateLimitRuleUpdate) -> RateLimitRuleResponse:
    """Update a RateLimitRule."""
    validate_rate_limit_rule_update(data)

    result = await db.execute(select(RateLimitRule).where(RateLimitRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise NotFoundError("RateLimitRule", str(rule_id))

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)

    return RateLimitRuleResponse.model_validate(rule)


async def delete_rate_limit_rule(db: AsyncSession, rule_id: int) -> None:
    """Delete a RateLimitRule."""
    result = await db.execute(select(RateLimitRule).where(RateLimitRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise NotFoundError("RateLimitRule", str(rule_id))

    await db.delete(rule)
    await db.commit()

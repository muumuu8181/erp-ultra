import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from shared.types import Base
from shared.errors import DuplicateError, NotFoundError
from src.foundation._004_api_gateway.models import GatewayRoute, RateLimitRule
from src.foundation._004_api_gateway.schemas import (
    GatewayRouteCreate, GatewayRouteUpdate,
    RateLimitRuleCreate, RateLimitRuleUpdate
)
from src.foundation._004_api_gateway import service


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_get_list_delete_gateway_route(db_session: AsyncSession):
    # Create
    create_data = GatewayRouteCreate(path="/api/test", target_url="http://test.com")
    route = await service.create_gateway_route(db_session, create_data)
    assert route.id is not None
    assert route.path == "/api/test"

    # Get
    fetched = await service.get_gateway_route(db_session, route.id)
    assert fetched.id == route.id

    # Duplicate
    with pytest.raises(DuplicateError):
        await service.create_gateway_route(db_session, create_data)

    # List
    paginated = await service.list_gateway_routes(db_session)
    assert paginated.total == 1
    assert len(paginated.items) == 1

    # Update
    update_data = GatewayRouteUpdate(target_url="http://new.com")
    updated = await service.update_gateway_route(db_session, route.id, update_data)
    assert updated.target_url == "http://new.com"
    assert updated.path == "/api/test"

    # Delete
    await service.delete_gateway_route(db_session, route.id)

    with pytest.raises(NotFoundError):
        await service.get_gateway_route(db_session, route.id)


@pytest.mark.asyncio
async def test_create_get_list_delete_rate_limit_rule(db_session: AsyncSession):
    # Create
    create_data = RateLimitRuleCreate(path="/api/test", max_requests=10, window_seconds=60)
    rule = await service.create_rate_limit_rule(db_session, create_data)
    assert rule.id is not None
    assert rule.max_requests == 10

    # Get
    fetched = await service.get_rate_limit_rule(db_session, rule.id)
    assert fetched.id == rule.id

    # List
    paginated = await service.list_rate_limit_rules(db_session)
    assert paginated.total == 1

    # Update
    update_data = RateLimitRuleUpdate(max_requests=20)
    updated = await service.update_rate_limit_rule(db_session, rule.id, update_data)
    assert updated.max_requests == 20
    assert updated.window_seconds == 60

    # Delete
    await service.delete_rate_limit_rule(db_session, rule.id)

    with pytest.raises(NotFoundError):
        await service.get_rate_limit_rule(db_session, rule.id)

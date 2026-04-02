import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import asyncio

from shared.types import Base
from src.foundation._008_cache.models import CacheEntry, CacheStatsRecord
from src.foundation._008_cache.schemas import CacheEntryCreate
from src.foundation._008_cache import service
from shared.errors import NotFoundError

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session

@pytest.fixture(autouse=True)
def clear_cache():
    service.clear_cache_state()
    yield

@pytest.mark.asyncio
async def test_set_success(db_session: AsyncSession):
    data = CacheEntryCreate(key="inventory:item:1", value='{"id": 1}', ttl_seconds=60, module="inventory")
    entry = await service.set(db_session, data)
    assert entry.key == "inventory:item:1"
    assert entry.value == '{"id": 1}'
    assert entry.module == "inventory"

    # Check memory
    assert service.get_cache_size() == 1

@pytest.mark.asyncio
async def test_set_updates_existing(db_session: AsyncSession):
    data = CacheEntryCreate(key="inventory:item:1", value='{"id": 1}', ttl_seconds=60, module="inventory")
    await service.set(db_session, data)

    data2 = CacheEntryCreate(key="inventory:item:1", value='{"id": 2}', ttl_seconds=60, module="inventory")
    entry = await service.set(db_session, data2)

    assert entry.value == '{"id": 2}'
    assert service.get_cache_size() == 1

@pytest.mark.asyncio
async def test_get_success(db_session: AsyncSession):
    data = CacheEntryCreate(key="inventory:item:1", value='{"id": 1}', ttl_seconds=60, module="inventory")
    await service.set(db_session, data)

    entry = await service.get(db_session, "inventory:item:1")
    assert entry.value == '{"id": 1}'
    assert entry.hit_count == 1

@pytest.mark.asyncio
async def test_get_hit_count_increments(db_session: AsyncSession):
    data = CacheEntryCreate(key="inventory:item:1", value='{"id": 1}', ttl_seconds=60, module="inventory")
    await service.set(db_session, data)

    await service.get(db_session, "inventory:item:1")
    entry = await service.get(db_session, "inventory:item:1")
    assert entry.hit_count == 2

@pytest.mark.asyncio
async def test_get_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await service.get(db_session, "inventory:item:missing")

@pytest.mark.asyncio
async def test_get_expired(db_session: AsyncSession, monkeypatch):
    data = CacheEntryCreate(key="inventory:item:1", value='{"id": 1}', ttl_seconds=1, module="inventory")
    await service.set(db_session, data)

    # Mock time
    future_time = datetime.utcnow() + timedelta(seconds=2)
    monkeypatch.setattr(service, "_get_now", lambda: future_time)

    with pytest.raises(NotFoundError):
        await service.get(db_session, "inventory:item:1")

@pytest.mark.asyncio
async def test_get_db_fallback(db_session: AsyncSession):
    data = CacheEntryCreate(key="inventory:item:1", value='{"id": 1}', ttl_seconds=60, module="inventory")
    await service.set(db_session, data)

    # Clear memory
    service.clear_cache_state()
    assert service.get_cache_size() == 0

    entry = await service.get(db_session, "inventory:item:1")
    assert entry.value == '{"id": 1}'
    assert service.get_cache_size() == 1

@pytest.mark.asyncio
async def test_delete_success(db_session: AsyncSession):
    data = CacheEntryCreate(key="inventory:item:1", value='{"id": 1}', ttl_seconds=60, module="inventory")
    await service.set(db_session, data)

    await service.delete(db_session, "inventory:item:1")
    assert service.get_cache_size() == 0

    with pytest.raises(NotFoundError):
        await service.get(db_session, "inventory:item:1")

@pytest.mark.asyncio
async def test_delete_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await service.delete(db_session, "inventory:item:missing")

@pytest.mark.asyncio
async def test_clear_by_module(db_session: AsyncSession):
    await service.set(db_session, CacheEntryCreate(key="inventory:item:1", value='{"id": 1}', ttl_seconds=60, module="inventory"))
    await service.set(db_session, CacheEntryCreate(key="orders:item:1", value='{"id": 1}', ttl_seconds=60, module="orders"))

    await service.clear_by_module(db_session, "inventory")

    assert service.get_cache_size() == 1
    with pytest.raises(NotFoundError):
        await service.get(db_session, "inventory:item:1")
    assert (await service.get(db_session, "orders:item:1")).value == '{"id": 1}'

@pytest.mark.asyncio
async def test_invalidate_pattern(db_session: AsyncSession):
    await service.set(db_session, CacheEntryCreate(key="inventory:products:1", value="1", ttl_seconds=60, module="inventory"))
    await service.set(db_session, CacheEntryCreate(key="inventory:categories:1", value="1", ttl_seconds=60, module="inventory"))
    await service.set(db_session, CacheEntryCreate(key="orders:1", value="1", ttl_seconds=60, module="orders"))

    await service.invalidate_pattern(db_session, "inventory:products:")

    assert service.get_cache_size() == 2
    with pytest.raises(NotFoundError):
        await service.get(db_session, "inventory:products:1")

@pytest.mark.asyncio
async def test_invalidate_pattern_with_wildcard(db_session: AsyncSession):
    await service.set(db_session, CacheEntryCreate(key="inventory:products:1", value="1", ttl_seconds=60, module="inventory"))

    await service.invalidate_pattern(db_session, "inventory:*")

    assert service.get_cache_size() == 0

@pytest.mark.asyncio
async def test_warm_cache(db_session: AsyncSession):
    entries = [
        CacheEntryCreate(key="inventory:1", value="1", ttl_seconds=60, module="inventory"),
        CacheEntryCreate(key="inventory:2", value="2", ttl_seconds=60, module="inventory")
    ]

    results = await service.warm_cache(db_session, entries)
    assert len(results) == 2
    assert service.get_cache_size() == 2

@pytest.mark.asyncio
async def test_cleanup_expired(db_session: AsyncSession, monkeypatch):
    await service.set(db_session, CacheEntryCreate(key="inventory:1", value="1", ttl_seconds=1, module="inventory"))
    await service.set(db_session, CacheEntryCreate(key="inventory:2", value="2", ttl_seconds=60, module="inventory"))

    future_time = datetime.utcnow() + timedelta(seconds=2)
    monkeypatch.setattr(service, "_get_now", lambda: future_time)

    await service.cleanup_expired(db_session)

    assert service.get_cache_size() == 1

@pytest.mark.asyncio
async def test_stats_hits_and_misses(db_session: AsyncSession):
    await service.set(db_session, CacheEntryCreate(key="inventory:1", value="1", ttl_seconds=60, module="inventory"))

    await service.get(db_session, "inventory:1")
    try:
        await service.get(db_session, "inventory:missing")
    except NotFoundError:
        pass

    stats = await service.get_stats(db_session, "inventory")
    assert len(stats) == 1
    assert stats[0].total_hits == 1
    assert stats[0].total_misses == 1

@pytest.mark.asyncio
async def test_flush_stats(db_session: AsyncSession):
    await service.set(db_session, CacheEntryCreate(key="inventory:1", value="1", ttl_seconds=60, module="inventory"))
    await service.get(db_session, "inventory:1")

    await service.flush_stats(db_session)

    stats = await service.get_stats(db_session, "inventory")
    assert len(stats[0].recent_stats) == 1
    assert stats[0].recent_stats[0].hits == 1

    # Counters should be reset
    assert service._stats_counters.get("inventory") is None

@pytest.mark.asyncio
async def test_lru_eviction_order(db_session: AsyncSession):
    await service.set(db_session, CacheEntryCreate(key="inventory:1", value="1", ttl_seconds=60, module="inventory"))
    await service.set(db_session, CacheEntryCreate(key="inventory:2", value="2", ttl_seconds=60, module="inventory"))

    # Access 1 to make it most recently used
    await service.get(db_session, "inventory:1")

    keys = list(service._cache_store.keys())
    assert keys[0] == "inventory:2" # Least recently used
    assert keys[1] == "inventory:1" # Most recently used

@pytest.mark.asyncio
async def test_clear_cache_state(db_session: AsyncSession):
    await service.set(db_session, CacheEntryCreate(key="inventory:1", value="1", ttl_seconds=60, module="inventory"))
    service.clear_cache_state()
    assert service.get_cache_size() == 0

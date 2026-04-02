import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from shared.errors import NotFoundError

from src.foundation._008_cache.models import CacheEntry, CacheStatsRecord
from src.foundation._008_cache.schemas import CacheEntryCreate
from src.foundation._008_cache.service import (
    get, set as cache_set, delete, clear_by_module,
    get_stats, invalidate_pattern, warm_cache,
    cleanup_expired, flush_stats, clear_cache_state,
    _cache_store, _stats_counters
)


@pytest.fixture(autouse=True)
def setup_teardown():
    clear_cache_state()
    yield
    clear_cache_state()


@pytest.mark.asyncio
async def test_set_success(db_session):
    data = CacheEntryCreate(
        key="inventory:test:1",
        value='{"a": 1}',
        ttl_seconds=3600,
        module="inventory"
    )
    entry = await cache_set(db_session, data)

    assert entry.key == "inventory:test:1"
    assert entry.value == '{"a": 1}'
    assert entry.module == "inventory"
    assert entry.id is not None

    # check memory
    assert "inventory:test:1" in _cache_store

    # check db
    result = await db_session.execute(select(CacheEntry).where(CacheEntry.key == "inventory:test:1"))
    db_entry = result.scalar_one()
    assert db_entry.value == '{"a": 1}'


@pytest.mark.asyncio
async def test_set_updates_existing(db_session):
    data1 = CacheEntryCreate(key="inventory:test:2", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    await cache_set(db_session, data1)

    data2 = CacheEntryCreate(key="inventory:test:2", value='{"a": 2}', ttl_seconds=7200, module="inventory")
    entry2 = await cache_set(db_session, data2)

    assert entry2.value == '{"a": 2}'
    assert entry2.ttl_seconds == 7200

    assert _cache_store["inventory:test:2"]["value"] == '{"a": 2}'


@pytest.mark.asyncio
async def test_get_success(db_session):
    data = CacheEntryCreate(key="inventory:test:3", value='{"a": 3}', ttl_seconds=3600, module="inventory")
    await cache_set(db_session, data)

    entry = await get(db_session, "inventory:test:3")
    assert entry.value == '{"a": 3}'
    assert entry.hit_count == 1


@pytest.mark.asyncio
async def test_get_hit_count_increments(db_session):
    data = CacheEntryCreate(key="inventory:test:4", value='{"a": 4}', ttl_seconds=3600, module="inventory")
    await cache_set(db_session, data)

    await get(db_session, "inventory:test:4")
    entry2 = await get(db_session, "inventory:test:4")

    assert entry2.hit_count == 2
    assert _stats_counters["inventory"]["hits"] == 2


@pytest.mark.asyncio
async def test_get_not_found(db_session):
    with pytest.raises(NotFoundError):
        await get(db_session, "inventory:test:not_found")


@pytest.mark.asyncio
async def test_get_expired(db_session):
    data = CacheEntryCreate(key="inventory:test:expired", value='{"a": 1}', ttl_seconds=1, module="inventory")
    entry = await cache_set(db_session, data)

    # modify memory to simulate expiration
    _cache_store["inventory:test:expired"]["expires_at"] = datetime.now() - timedelta(seconds=10)

    with pytest.raises(NotFoundError):
        await get(db_session, "inventory:test:expired")

    assert "inventory:test:expired" not in _cache_store
    assert _stats_counters["inventory"]["misses"] == 1
    assert _stats_counters["inventory"]["evictions"] == 1


@pytest.mark.asyncio
async def test_get_db_fallback(db_session):
    # Set directly in DB
    now = datetime.now()
    entry = CacheEntry(
        key="inventory:test:fallback",
        value='{"a": 1}',
        ttl_seconds=3600,
        expires_at=now + timedelta(seconds=3600),
        module="inventory"
    )
    db_session.add(entry)
    await db_session.commit()

    assert "inventory:test:fallback" not in _cache_store

    result = await get(db_session, "inventory:test:fallback")
    assert result.value == '{"a": 1}'
    assert "inventory:test:fallback" in _cache_store
    assert _stats_counters["inventory"]["hits"] == 1


@pytest.mark.asyncio
async def test_delete_success(db_session):
    data = CacheEntryCreate(key="inventory:test:del", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    await cache_set(db_session, data)

    await delete(db_session, "inventory:test:del")

    assert "inventory:test:del" not in _cache_store

    result = await db_session.execute(select(CacheEntry).where(CacheEntry.key == "inventory:test:del"))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_not_found(db_session):
    with pytest.raises(NotFoundError):
        await delete(db_session, "inventory:test:notfound")


@pytest.mark.asyncio
async def test_clear_by_module(db_session):
    data1 = CacheEntryCreate(key="inventory:test:c1", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    data2 = CacheEntryCreate(key="system:test:c2", value='{"a": 2}', ttl_seconds=3600, module="system")
    await cache_set(db_session, data1)
    await cache_set(db_session, data2)

    count = await clear_by_module(db_session, "inventory")
    assert count == 1

    assert "inventory:test:c1" not in _cache_store
    assert "system:test:c2" in _cache_store


@pytest.mark.asyncio
async def test_invalidate_pattern(db_session):
    data1 = CacheEntryCreate(key="inventory:products:1", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    data2 = CacheEntryCreate(key="inventory:categories:2", value='{"a": 2}', ttl_seconds=3600, module="inventory")
    data3 = CacheEntryCreate(key="system:config:1", value='{"a": 3}', ttl_seconds=3600, module="system")

    await cache_set(db_session, data1)
    await cache_set(db_session, data2)
    await cache_set(db_session, data3)

    count = await invalidate_pattern(db_session, "inventory:products")
    assert count == 1

    assert "inventory:products:1" not in _cache_store
    assert "inventory:categories:2" in _cache_store


@pytest.mark.asyncio
async def test_invalidate_pattern_with_wildcard(db_session):
    data1 = CacheEntryCreate(key="inventory:products:1", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    data2 = CacheEntryCreate(key="inventory:categories:2", value='{"a": 2}', ttl_seconds=3600, module="inventory")
    await cache_set(db_session, data1)
    await cache_set(db_session, data2)

    count = await invalidate_pattern(db_session, "inventory:*")
    assert count == 2


@pytest.mark.asyncio
async def test_warm_cache(db_session):
    entries = [
        CacheEntryCreate(key="inventory:w1", value='{"a": 1}', ttl_seconds=3600, module="inventory"),
        CacheEntryCreate(key="inventory:w2", value='{"a": 2}', ttl_seconds=3600, module="inventory")
    ]

    results = await warm_cache(db_session, entries)
    assert len(results) == 2
    assert "inventory:w1" in _cache_store
    assert "inventory:w2" in _cache_store


@pytest.mark.asyncio
async def test_cleanup_expired(db_session):
    data1 = CacheEntryCreate(key="inventory:exp1", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    await cache_set(db_session, data1)

    # DB entry that is already expired
    # In SQLite async tests, using datetime.now() can have timing issues where the cleanup task
    # gets a slightly older `now()` if it runs too fast, or vice versa. Let's make it explicitly very expired.
    now = datetime.now()
    entry = CacheEntry(
        key="inventory:exp2",
        value='{"a": 2}',
        ttl_seconds=3600,
        expires_at=now - timedelta(days=1),
        module="inventory"
    )
    db_session.add(entry)
    await db_session.commit()

    # Make memory entry explicitly very expired
    _cache_store["inventory:exp1"]["expires_at"] = now - timedelta(days=1)

    # We also need to manually update the DB entry for exp1 to be expired,
    # since cleanup_expired deletes from DB based on DB's expires_at, not memory's!
    result = await db_session.execute(select(CacheEntry).where(CacheEntry.key == "inventory:exp1"))
    db_entry1 = result.scalar_one()
    db_entry1.expires_at = now - timedelta(days=1)
    await db_session.commit()

    count = await cleanup_expired(db_session)
    assert count == 2
    assert "inventory:exp1" not in _cache_store

    result = await db_session.execute(select(CacheEntry))
    assert len(result.scalars().all()) == 0


@pytest.mark.asyncio
async def test_stats_hits_and_misses(db_session):
    data = CacheEntryCreate(key="inventory:stat1", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    await cache_set(db_session, data)

    await get(db_session, "inventory:stat1")
    await get(db_session, "inventory:stat1")

    with pytest.raises(NotFoundError):
        await get(db_session, "inventory:stat_missing")

    stats = await get_stats(db_session, "inventory")
    assert len(stats) == 1
    assert stats[0].total_hits == 2
    assert stats[0].total_misses == 1
    assert stats[0].hit_rate == (2/3) * 100


@pytest.mark.asyncio
async def test_flush_stats(db_session):
    data = CacheEntryCreate(key="inventory:stat_flush", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    await cache_set(db_session, data)

    await get(db_session, "inventory:stat_flush")
    assert _stats_counters["inventory"]["hits"] == 1

    await flush_stats(db_session)

    assert _stats_counters["inventory"]["hits"] == 0

    result = await db_session.execute(select(CacheStatsRecord))
    records = result.scalars().all()
    assert len(records) == 1
    assert records[0].hits == 1


@pytest.mark.asyncio
async def test_lru_eviction_order(db_session):
    data1 = CacheEntryCreate(key="inventory:lru:1", value='{"a": 1}', ttl_seconds=3600, module="inventory")
    data2 = CacheEntryCreate(key="inventory:lru:2", value='{"a": 2}', ttl_seconds=3600, module="inventory")

    await cache_set(db_session, data1)
    await cache_set(db_session, data2)

    keys = list(_cache_store.keys())
    assert keys[0] == "inventory:lru:1"
    assert keys[1] == "inventory:lru:2"

    await get(db_session, "inventory:lru:1")

    keys_after = list(_cache_store.keys())
    assert keys_after[0] == "inventory:lru:2"
    assert keys_after[1] == "inventory:lru:1"


def test_clear_cache_state():
    _cache_store["test"] = {}
    _stats_counters["test"] = {}

    clear_cache_state()

    assert len(_cache_store) == 0
    assert len(_stats_counters) == 0

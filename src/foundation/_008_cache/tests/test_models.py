import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.foundation._008_cache.models import CacheEntry, CacheStatsRecord

@pytest.mark.asyncio
async def test_cache_entry_creation(db_session):
    now = datetime.now()
    entry = CacheEntry(
        key="inventory:products:123",
        value='{"name": "test"}',
        ttl_seconds=3600,
        expires_at=now + timedelta(seconds=3600),
        module="inventory"
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    assert entry.id is not None
    assert entry.key == "inventory:products:123"
    assert entry.value == '{"name": "test"}'
    assert entry.ttl_seconds == 3600
    assert entry.module == "inventory"
    assert entry.hit_count == 0  # Default value
    assert entry.created_at is not None
    assert entry.updated_at is not None

@pytest.mark.asyncio
async def test_cache_entry_unique_key(db_session):
    now = datetime.now()
    entry1 = CacheEntry(
        key="unique:key",
        value='{"name": "test1"}',
        ttl_seconds=3600,
        expires_at=now + timedelta(seconds=3600),
        module="system"
    )
    db_session.add(entry1)
    await db_session.commit()

    entry2 = CacheEntry(
        key="unique:key",
        value='{"name": "test2"}',
        ttl_seconds=3600,
        expires_at=now + timedelta(seconds=3600),
        module="system"
    )
    db_session.add(entry2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_cache_stats_record_creation(db_session):
    record = CacheStatsRecord(
        module="inventory",
        hits=10,
        misses=2,
        evictions=1
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)

    assert record.id is not None
    assert record.module == "inventory"
    assert record.hits == 10
    assert record.misses == 2
    assert record.evictions == 1
    assert record.recorded_at is not None

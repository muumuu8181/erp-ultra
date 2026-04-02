import pytest
from datetime import datetime
from src.foundation._008_cache.models import CacheEntry, CacheStatsRecord

def test_cache_entry_creation():
    entry = CacheEntry(
        key="inventory:products:123",
        value='{"id": 123}',
        ttl_seconds=60,
        expires_at=datetime.utcnow(),
        module="inventory",
        hit_count=0
    )
    assert entry.key == "inventory:products:123"
    assert entry.module == "inventory"
    assert entry.hit_count == 0

def test_cache_stats_record_creation():
    record = CacheStatsRecord(
        module="inventory",
        hits=10,
        misses=2,
        evictions=1
    )
    assert record.module == "inventory"
    assert record.hits == 10
    assert record.misses == 2
    assert record.evictions == 1

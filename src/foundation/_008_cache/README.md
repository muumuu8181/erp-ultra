# Phase 0: Caching Layer (`_008_cache`)

This module provides an in-memory LRU cache with TTL support, cache hit/miss tracking per module, pattern-based invalidation, and a background cleanup task for expired entries.

## Usage

```python
from src.foundation._008_cache import service
from src.foundation._008_cache.schemas import CacheEntryCreate

# Set a cache entry
await service.set(db, CacheEntryCreate(
    key="inventory:products:123",
    value='{"id": 123, "name": "Product"}',
    ttl_seconds=3600,
    module="inventory"
))

# Get a cache entry
entry = await service.get(db, "inventory:products:123")
```

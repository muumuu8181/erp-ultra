# Caching Layer Module (`_008_cache`)

This module provides an in-memory LRU cache with TTL support, cache hit/miss tracking per module, pattern-based invalidation, and a background cleanup task for expired entries.

## Features
- In-memory LRU cache using `OrderedDict`
- Database fallback for cache misses
- TTL support with background cleanup
- Statistics tracking per module (hits, misses, evictions, hit rate)
- Pattern-based cache invalidation (e.g. `inventory:*`)
- Endpoints for manual cache clearing, invalidating, warming, and cleanup

## Models
- `CacheEntry`: Stores the cached value, TTL, expiry time, module, and hit count.
- `CacheStatsRecord`: Stores historical aggregated cache hit/miss statistics by module.

## Endpoints
Prefix: `/api/v1/cache`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{key}` | Get cache entry |
| PUT | `/{key}` | Set cache entry |
| DELETE | `/{key}` | Delete cache entry |
| DELETE | `/` | Clear cache by module |
| POST | `/invalidate` | Invalidate by pattern |
| GET | `/stats` | Get cache statistics |
| POST | `/warm` | Warm cache with entries |
| POST | `/cleanup` | Trigger manual cleanup |

## Usage
The `start_cleanup_task` should be registered with the FastAPI application lifecycle (lifespan) to run the background job that cleans up expired cache entries and flushes in-memory stats to the DB periodically.

Example usage in router:
```python
from src.foundation._008_cache.service import get, set as cache_set
```
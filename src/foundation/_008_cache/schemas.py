from datetime import datetime
from pydantic import Field
from shared.types import BaseSchema

class CacheEntryCreate(BaseSchema):
    """Schema for creating/updating a cache entry."""
    key: str
    value: str  # Must be valid JSON
    ttl_seconds: int
    module: str

class CacheEntryUpdate(BaseSchema):
    """Schema for updating a cache entry."""
    value: str | None = None  # Must be valid JSON if provided
    ttl_seconds: int | None = None

class CacheEntryResponse(BaseSchema):
    """Schema for cache entry response."""
    id: int
    key: str
    value: str
    ttl_seconds: int
    expires_at: datetime
    module: str
    hit_count: int
    created_at: datetime
    updated_at: datetime

class CacheStatsRecordResponse(BaseSchema):
    """Schema for a single stats record."""
    id: int
    module: str
    hits: int
    misses: int
    evictions: int
    recorded_at: datetime

class CacheStatsResponse(BaseSchema):
    """Schema for cache statistics response."""
    module: str
    total_hits: int
    total_misses: int
    total_evictions: int
    hit_rate: float  # hits / (hits + misses) as percentage
    entry_count: int
    recent_stats: list[CacheStatsRecordResponse]

class CacheBulkDelete(BaseSchema):
    """Schema for bulk cache deletion."""
    keys: list[str]

class CacheInvalidateRequest(BaseSchema):
    """Schema for pattern-based invalidation."""
    pattern: str  # Prefix pattern, e.g. "inventory:*" or "orders:customer:123"

class CacheWarmRequest(BaseSchema):
    """Schema for cache warming."""
    entries: list[CacheEntryCreate]

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.foundation._001_database.engine import get_db
from src.foundation._008_cache.schemas import (
    CacheEntryCreate, CacheEntryResponse, CacheInvalidateRequest,
    CacheWarmRequest, CacheStatsResponse
)
from src.foundation._008_cache import service

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])

@router.delete("/")
async def clear_cache_by_module(module: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Clear cache entries by module."""
    count = await service.clear_by_module(db, module)
    return {"cleared_count": count}

@router.get("/stats", response_model=List[CacheStatsResponse])
async def get_cache_stats(module: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Get cache statistics."""
    return await service.get_stats(db, module)

@router.get("/{key}", response_model=CacheEntryResponse)
async def get_cache_entry(key: str, db: AsyncSession = Depends(get_db)):
    """Get a cache entry by key."""
    return await service.get(db, key)

@router.put("/{key}", response_model=CacheEntryResponse)
async def set_cache_entry(key: str, data: CacheEntryCreate, db: AsyncSession = Depends(get_db)):
    """Set a cache entry."""
    # Ensure key in URL matches payload or just use URL key
    data.key = key
    return await service.set(db, data)

@router.delete("/{key}")
async def delete_cache_entry(key: str, db: AsyncSession = Depends(get_db)):
    """Delete a cache entry."""
    await service.delete(db, key)
    return {"message": "Cache entry deleted"}

@router.post("/invalidate")
async def invalidate_cache_pattern(req: CacheInvalidateRequest, db: AsyncSession = Depends(get_db)):
    """Invalidate cache entries by pattern."""
    count = await service.invalidate_pattern(db, req.pattern)
    return {"invalidated_count": count}

@router.post("/warm", response_model=List[CacheEntryResponse])
async def warm_cache(req: CacheWarmRequest, db: AsyncSession = Depends(get_db)):
    """Warm the cache with multiple entries."""
    return await service.warm_cache(db, req.entries)

@router.post("/cleanup")
async def trigger_manual_cleanup(db: AsyncSession = Depends(get_db)):
    """Manually trigger expired cache cleanup."""
    count = await service.cleanup_expired(db)
    return {"cleaned_count": count}

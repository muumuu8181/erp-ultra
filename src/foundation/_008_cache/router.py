from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import get_db

from .schemas import (
    CacheEntryCreate,
    CacheEntryResponse,
    CacheStatsResponse,
    CacheInvalidateRequest,
    CacheWarmRequest
)
from .service import (
    get,
    set,
    delete,
    clear_by_module,
    get_stats,
    invalidate_pattern,
    warm_cache,
    cleanup_expired
)

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])


@router.get("/stats", response_model=list[CacheStatsResponse])
async def get_cache_stats(
    module: Optional[str] = Query(None, description="Filter stats by module"),
    db: AsyncSession = Depends(get_db)
):
    """Get cache statistics."""
    return await get_stats(db, module=module)


@router.post("/invalidate", response_model=dict)
async def invalidate_cache_pattern(
    request: CacheInvalidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Invalidate cache entries matching a pattern."""
    count = await invalidate_pattern(db, request.pattern)
    return {"invalidated_count": count}


@router.post("/warm", response_model=list[CacheEntryResponse])
async def warm_cache_endpoint(
    request: CacheWarmRequest,
    db: AsyncSession = Depends(get_db)
):
    """Pre-populate cache with multiple entries."""
    return await warm_cache(db, request.entries)


@router.post("/cleanup", response_model=dict)
async def manual_cleanup(
    db: AsyncSession = Depends(get_db)
):
    """Trigger manual cleanup of expired cache entries."""
    count = await cleanup_expired(db)
    return {"cleaned_count": count}


@router.delete("/", response_model=dict)
async def clear_cache_by_module(
    module: str = Query(..., description="Module to clear cache for"),
    db: AsyncSession = Depends(get_db)
):
    """Clear all cache entries for a module."""
    count = await clear_by_module(db, module)
    return {"cleared_count": count}


@router.get("/{key:path}", response_model=CacheEntryResponse)
async def get_cache_entry(
    key: str = Path(..., description="Cache key to retrieve"),
    db: AsyncSession = Depends(get_db)
):
    """Get a cache entry."""
    from fastapi import HTTPException
    from shared.errors import NotFoundError
    try:
        return await get(db, key)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{key:path}", response_model=CacheEntryResponse)
async def set_cache_entry(
    key: str = Path(..., description="Cache key to set"),
    data: CacheEntryCreate = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Set a cache entry."""
    # Ensure the key in path matches the body, path takes precedence as requested
    data.key = key
    return await set(db, data)


@router.delete("/{key:path}", response_model=dict)
async def delete_cache_entry(
    key: str = Path(..., description="Cache key to delete"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a cache entry."""
    from fastapi import HTTPException
    from shared.errors import NotFoundError
    try:
        await delete(db, key)
        return {"message": "Cache entry deleted"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

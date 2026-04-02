import asyncio
import sys
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete, update, desc, func
import logging

from shared.errors import NotFoundError
from src.foundation._008_cache.models import CacheEntry, CacheStatsRecord
from src.foundation._008_cache.schemas import (
    CacheEntryCreate, CacheStatsResponse, CacheStatsRecordResponse
)
from src.foundation._008_cache.validators import (
    validate_cache_key, validate_cache_value, validate_ttl, validate_module_name
)

logger = logging.getLogger(__name__)

# In-memory LRU cache: OrderedDict[key] -> {value, expires_at, module, hit_count}
_cache_store: OrderedDict[str, dict] = OrderedDict()

# Module-level stats tracking (in-memory, periodically flushed to DB)
_stats_counters: dict[str, dict[str, int]] = {}  # {module: {"hits": N, "misses": N, "evictions": N}}

def _get_now() -> datetime:
    # Use timezone-naive UTC to match typical SQLAlchemy setups or just naive local.
    # Usually `func.now()` is naive UTC or naive local. We'll use naive UTC.
    return datetime.utcnow()

def _init_stats(module: str) -> None:
    if module not in _stats_counters:
        _stats_counters[module] = {"hits": 0, "misses": 0, "evictions": 0}

def _increment_stat(module: str, stat_type: str) -> None:
    _init_stats(module)
    _stats_counters[module][stat_type] += 1

async def get(db: AsyncSession, key: str) -> CacheEntry:
    """
    Get a value from cache.
    """
    now = _get_now()

    # 1. Check in-memory
    if key in _cache_store:
        entry_data = _cache_store[key]
        module = entry_data["module"]

        if entry_data["expires_at"] > now:
            # Hit
            _cache_store.move_to_end(key)
            entry_data["hit_count"] += 1
            _increment_stat(module, "hits")

            # Re-fetch from DB to get full object with id, created_at, updated_at
            # to satisfy Pydantic response models, or fetch from DB if needed.
            result = await db.execute(select(CacheEntry).where(CacheEntry.key == key))
            db_entry = result.scalar_one_or_none()
            if db_entry:
                db_entry.hit_count = entry_data["hit_count"]
                return db_entry

            # Fallback if somehow not in DB but in memory (shouldn't happen)
            return CacheEntry(
                id=0, # Fake ID
                key=key,
                value=entry_data["value"],
                ttl_seconds=int((entry_data["expires_at"] - now).total_seconds()),
                expires_at=entry_data["expires_at"],
                module=module,
                hit_count=entry_data["hit_count"],
                created_at=now,
                updated_at=now
            )
        else:
            # Expired
            del _cache_store[key]
            _increment_stat(module, "evictions")
            _increment_stat(module, "misses")

    # 2. Check DB
    result = await db.execute(select(CacheEntry).where(CacheEntry.key == key))
    db_entry = result.scalar_one_or_none()

    if db_entry:
        module = db_entry.module
        if db_entry.expires_at > now:
            # Load into memory
            _cache_store[key] = {
                "value": db_entry.value,
                "expires_at": db_entry.expires_at,
                "module": module,
                "hit_count": db_entry.hit_count + 1
            }
            # Hit
            _increment_stat(module, "hits")

            # Update DB hit count (fire and forget conceptually, but we await)
            db_entry.hit_count += 1
            await db.commit()
            await db.refresh(db_entry)
            return db_entry
        else:
            # Expired in DB
            await db.execute(sql_delete(CacheEntry).where(CacheEntry.key == key))
            await db.commit()
            _increment_stat(module, "misses")
            raise NotFoundError(f"Cache entry not found or expired: {key}")

    # 3. Not found anywhere
    # If it was never in cache, we don't know the module, but we might guess from key prefix
    module_guess = key.split(':')[0] if ':' in key else "unknown"
    _increment_stat(module_guess, "misses")
    raise NotFoundError(f"Cache entry not found: {key}")

async def set(db: AsyncSession, data: CacheEntryCreate) -> CacheEntry:
    """
    Set a cache value.
    """
    validate_cache_key(data.key)
    validate_cache_value(data.value)
    validate_ttl(data.ttl_seconds)
    validate_module_name(data.module)

    now = _get_now()
    expires_at = now + timedelta(seconds=data.ttl_seconds)

    # Update memory
    _cache_store[data.key] = {
        "value": data.value,
        "expires_at": expires_at,
        "module": data.module,
        "hit_count": 0
    }
    _cache_store.move_to_end(data.key)

    # Upsert in DB
    result = await db.execute(select(CacheEntry).where(CacheEntry.key == data.key))
    db_entry = result.scalar_one_or_none()

    if db_entry:
        db_entry.value = data.value
        db_entry.ttl_seconds = data.ttl_seconds
        db_entry.expires_at = expires_at
        db_entry.module = data.module
        db_entry.hit_count = 0 # Reset hit count on new value?
    else:
        db_entry = CacheEntry(
            key=data.key,
            value=data.value,
            ttl_seconds=data.ttl_seconds,
            expires_at=expires_at,
            module=data.module,
            hit_count=0
        )
        db.add(db_entry)

    await db.commit()
    await db.refresh(db_entry)
    return db_entry

async def delete(db: AsyncSession, key: str) -> None:
    """
    Delete a cache entry.
    """
    found_in_mem = False
    if key in _cache_store:
        del _cache_store[key]
        found_in_mem = True

    result = await db.execute(sql_delete(CacheEntry).where(CacheEntry.key == key))
    deleted_count = result.rowcount
    await db.commit()

    if not found_in_mem and deleted_count == 0:
        raise NotFoundError(f"Cache entry not found: {key}")

async def clear_by_module(db: AsyncSession, module: str) -> int:
    """
    Clear all cache entries for a module.
    """
    # Clear memory
    keys_to_delete = [k for k, v in _cache_store.items() if v["module"] == module]
    for k in keys_to_delete:
        del _cache_store[k]

    # Clear DB
    result = await db.execute(sql_delete(CacheEntry).where(CacheEntry.module == module))
    await db.commit()

    # Return max of memory vs db in case of sync issues, or just DB count if accurate.
    # Usually keys_to_delete represents what we had active. We'll return DB count.
    return result.rowcount

async def get_stats(db: AsyncSession, module: str | None = None) -> list[CacheStatsResponse]:
    """
    Get cache statistics.
    """
    modules_to_query = [module] if module else list(_stats_counters.keys())

    # If no module requested and _stats_counters is empty, we might still want to fetch from DB
    if not module:
        db_modules = await db.execute(select(CacheStatsRecord.module).distinct())
        modules_to_query.extend([row[0] for row in db_modules.all()])

        # Use a list comprehension to preserve order while deduplicating, or just built-in set if not shadowing
        import builtins
        seen = builtins.set()
        deduped = []
        for m in modules_to_query:
            if m not in seen:
                seen.add(m)
                deduped.append(m)
        modules_to_query = deduped

    response = []
    now = _get_now()

    for mod in modules_to_query:
        # Get DB stats
        db_stats = await db.execute(
            select(CacheStatsRecord)
            .where(CacheStatsRecord.module == mod)
            .order_by(desc(CacheStatsRecord.recorded_at))
            .limit(10)
        )
        recent = db_stats.scalars().all()

        # Calculate totals
        total_hits = sum(r.hits for r in recent)
        total_misses = sum(r.misses for r in recent)
        total_evictions = sum(r.evictions for r in recent)

        # Add in-memory current
        if mod in _stats_counters:
            total_hits += _stats_counters[mod]["hits"]
            total_misses += _stats_counters[mod]["misses"]
            total_evictions += _stats_counters[mod]["evictions"]

        hit_rate = 0.0
        if total_hits + total_misses > 0:
            hit_rate = (total_hits / (total_hits + total_misses)) * 100.0

        # Count active entries
        active_mem = sum(1 for v in _cache_store.values() if v["module"] == mod and v["expires_at"] > now)

        # Or from DB (for simplicity, we use DB count of non-expired)
        db_active = await db.execute(
            select(func.count(CacheEntry.id))
            .where(CacheEntry.module == mod)
            .where(CacheEntry.expires_at > now)
        )
        entry_count = db_active.scalar() or 0

        recent_resp = [
            CacheStatsRecordResponse(
                id=r.id,
                module=r.module,
                hits=r.hits,
                misses=r.misses,
                evictions=r.evictions,
                recorded_at=r.recorded_at
            ) for r in recent
        ]

        response.append(CacheStatsResponse(
            module=mod,
            total_hits=total_hits,
            total_misses=total_misses,
            total_evictions=total_evictions,
            hit_rate=hit_rate,
            entry_count=entry_count,
            recent_stats=recent_resp
        ))

    return response

async def invalidate_pattern(db: AsyncSession, pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    """
    if pattern.endswith('*'):
        prefix = pattern[:-1]
    else:
        prefix = pattern

    # In-memory
    keys_to_delete = [k for k in _cache_store.keys() if k.startswith(prefix)]
    for k in keys_to_delete:
        del _cache_store[k]

    # DB
    result = await db.execute(sql_delete(CacheEntry).where(CacheEntry.key.startswith(prefix)))
    await db.commit()

    return result.rowcount

async def warm_cache(db: AsyncSession, entries: list[CacheEntryCreate]) -> list[CacheEntry]:
    """
    Pre-populate cache with multiple entries.
    """
    results = []
    for entry_data in entries:
        entry = await set(db, entry_data)
        results.append(entry)
    return results

async def cleanup_expired(db: AsyncSession) -> int:
    """
    Background task: remove expired entries from memory and DB.
    """
    now = _get_now()

    # In-memory
    keys_to_delete = []
    for k, v in _cache_store.items():
        if v["expires_at"] < now:
            keys_to_delete.append(k)
            _increment_stat(v["module"], "evictions")

    for k in keys_to_delete:
        del _cache_store[k]

    # DB
    result = await db.execute(sql_delete(CacheEntry).where(CacheEntry.expires_at < now))
    await db.commit()

    return result.rowcount

async def flush_stats(db: AsyncSession) -> None:
    """
    Flush in-memory stats counters to DB.
    """
    global _stats_counters

    for module, counters in _stats_counters.items():
        if counters["hits"] > 0 or counters["misses"] > 0 or counters["evictions"] > 0:
            record = CacheStatsRecord(
                module=module,
                hits=counters["hits"],
                misses=counters["misses"],
                evictions=counters["evictions"]
            )
            db.add(record)

    await db.commit()
    # Reset
    _stats_counters = {}

def clear_cache_state() -> None:
    """
    Clear all in-memory cache and stats state.
    """
    global _stats_counters, _cache_store
    _cache_store.clear()
    _stats_counters.clear()

def get_cache_size() -> int:
    """
    Return number of entries in in-memory cache.
    """
    return len(_cache_store)

def get_memory_usage_estimate() -> int:
    """
    Estimate memory usage of in-memory cache in bytes.
    """
    return sum(sys.getsizeof(k) + sys.getsizeof(v["value"]) for k, v in _cache_store.items())

async def start_cleanup_task(db_session_factory, interval_seconds: int = 60) -> None:
    """
    Periodic task that runs cleanup_expired and flush_stats.
    """
    while True:
        try:
            async with db_session_factory() as db:
                await cleanup_expired(db)
                await flush_stats(db)
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}")
        await asyncio.sleep(interval_seconds)

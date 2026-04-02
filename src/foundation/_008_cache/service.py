from collections import OrderedDict
from datetime import datetime, timedelta
import asyncio
import logging
from sqlalchemy import select, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.errors import NotFoundError
from .models import CacheEntry, CacheStatsRecord
from .schemas import CacheEntryCreate, CacheStatsResponse, CacheStatsRecordResponse
from .validators import validate_cache_key, validate_cache_value, validate_ttl, validate_module_name

# In-memory LRU cache: OrderedDict[key] -> {value, expires_at, module, hit_count, id, created_at, updated_at}
_cache_store: OrderedDict[str, dict] = OrderedDict()

# Module-level stats tracking (in-memory, periodically flushed to DB)
_stats_counters: dict[str, dict[str, int]] = {}  # {module: {"hits": N, "misses": N, "evictions": N}}


def _init_module_stats(module: str) -> None:
    """Initialize stats counters for a module if not exists."""
    if module not in _stats_counters:
        _stats_counters[module] = {"hits": 0, "misses": 0, "evictions": 0}


async def get(db: AsyncSession, key: str) -> CacheEntry:
    """
    Get a value from cache.
    - Check in-memory cache first
    - If found and not expired:
      1. Move to end of OrderedDict (LRU update)
      2. Increment hit_count
      3. Increment module stats hits
      4. Return CacheEntry
    - If expired: remove from cache, increment misses, record eviction
    - If not found in memory: check DB (fallback)
      - If in DB and not expired: load into memory, return
      - If in DB but expired: delete from DB, record miss
    - If not found anywhere: increment misses, raise NotFoundError
    """
    now = datetime.now()

    # Check memory first
    if key in _cache_store:
        entry_dict = _cache_store[key]
        module = entry_dict["module"]
        _init_module_stats(module)

        if entry_dict["expires_at"] > now:
            # Hit! Update LRU
            _cache_store.move_to_end(key)
            entry_dict["hit_count"] += 1
            _stats_counters[module]["hits"] += 1

            # Construct and return CacheEntry instance
            return CacheEntry(
                id=entry_dict["id"],
                key=key,
                value=entry_dict["value"],
                ttl_seconds=entry_dict["ttl_seconds"],
                expires_at=entry_dict["expires_at"],
                module=module,
                hit_count=entry_dict["hit_count"],
                created_at=entry_dict["created_at"],
                updated_at=entry_dict["updated_at"]
            )
        else:
            # Expired in memory
            del _cache_store[key]
            _stats_counters[module]["misses"] += 1
            _stats_counters[module]["evictions"] += 1

            # Remove from DB as well
            from sqlalchemy import delete as sql_delete
            await db.execute(sql_delete(CacheEntry).where(CacheEntry.key == key))
            await db.commit()
            raise NotFoundError(f"Cache entry with key '{key}' not found or expired")

    # DB fallback
    result = await db.execute(select(CacheEntry).where(CacheEntry.key == key))
    db_entry = result.scalar_one_or_none()

    if db_entry:
        module = db_entry.module
        _init_module_stats(module)

        if db_entry.expires_at > now:
            # Hit in DB, not in memory. Load to memory.
            db_entry.hit_count += 1
            _stats_counters[module]["hits"] += 1

            _cache_store[key] = {
                "id": db_entry.id,
                "value": db_entry.value,
                "ttl_seconds": db_entry.ttl_seconds,
                "expires_at": db_entry.expires_at,
                "module": module,
                "hit_count": db_entry.hit_count,
                "created_at": db_entry.created_at,
                "updated_at": db_entry.updated_at
            }
            # Commit the updated hit count to DB
            await db.commit()
            await db.refresh(db_entry)
            return CacheEntry(
                id=db_entry.id,
                key=db_entry.key,
                value=db_entry.value,
                ttl_seconds=db_entry.ttl_seconds,
                expires_at=db_entry.expires_at,
                module=db_entry.module,
                hit_count=db_entry.hit_count,
                created_at=db_entry.created_at,
                updated_at=db_entry.updated_at
            )
        else:
            # Expired in DB
            _stats_counters[module]["misses"] += 1
            from sqlalchemy import delete as sql_delete
            await db.execute(sql_delete(CacheEntry).where(CacheEntry.key == key))
            await db.commit()
            raise NotFoundError(f"Cache entry with key '{key}' not found or expired")

    # Not found anywhere
    # For misses on non-existent keys, we can't easily attribute to a module without parsing key
    # Let's try to extract module from key if possible
    # Use exact key extraction
    try:
        segments = key.split(":")
        if len(segments) > 1: # We need at least 2 segments
            module_guess = segments[0]
            _init_module_stats(module_guess)
            _stats_counters[module_guess]["misses"] += 1
    except Exception:
        pass

    raise NotFoundError(f"Cache entry with key '{key}' not found")


async def set(db: AsyncSession, data: CacheEntryCreate) -> CacheEntry:
    """
    Set a cache value.
    - Validate key, value, ttl, module
    - Calculate expires_at = now + ttl_seconds
    - Store in in-memory OrderedDict (move to end = most recently used)
    - Upsert in DB (create or update)
    - Return CacheEntry
    """
    validate_cache_key(data.key)
    validate_cache_value(data.value)
    validate_ttl(data.ttl_seconds)
    validate_module_name(data.module)

    now = datetime.now()
    expires_at = now + timedelta(seconds=data.ttl_seconds)

    # Upsert in DB
    result = await db.execute(select(CacheEntry).where(CacheEntry.key == data.key))
    db_entry = result.scalar_one_or_none()

    if db_entry:
        db_entry.value = data.value
        db_entry.ttl_seconds = data.ttl_seconds
        db_entry.expires_at = expires_at
        db_entry.module = data.module
        db_entry.updated_at = now
    else:
        db_entry = CacheEntry(
            key=data.key,
            value=data.value,
            ttl_seconds=data.ttl_seconds,
            expires_at=expires_at,
            module=data.module,
            hit_count=0,
            created_at=now,
            updated_at=now
        )
        db.add(db_entry)

    await db.commit()
    await db.refresh(db_entry)

    detached_entry = CacheEntry(
        id=db_entry.id,
        key=db_entry.key,
        value=db_entry.value,
        ttl_seconds=db_entry.ttl_seconds,
        expires_at=db_entry.expires_at,
        module=db_entry.module,
        hit_count=db_entry.hit_count,
        created_at=db_entry.created_at,
        updated_at=db_entry.updated_at
    )

    # Store in memory
    if data.key in _cache_store:
        del _cache_store[data.key] # remove to put at end later

    _cache_store[data.key] = {
        "id": detached_entry.id,
        "value": detached_entry.value,
        "ttl_seconds": detached_entry.ttl_seconds,
        "expires_at": detached_entry.expires_at,
        "module": detached_entry.module,
        "hit_count": detached_entry.hit_count,
        "created_at": detached_entry.created_at,
        "updated_at": detached_entry.updated_at
    }

    return detached_entry


async def delete(db: AsyncSession, key: str) -> None:
    """
    Delete a cache entry.
    - Remove from in-memory cache
    - Delete from DB
    - Raise NotFoundError if key does not exist
    """
    found_in_memory = False
    if key in _cache_store:
        del _cache_store[key]
        found_in_memory = True

    result = await db.execute(select(CacheEntry).where(CacheEntry.key == key))
    db_entry = result.scalar_one_or_none()

    if not db_entry and not found_in_memory:
        raise NotFoundError(f"Cache entry with key '{key}' not found")

    if db_entry:
        from sqlalchemy import delete as sql_delete
        await db.execute(sql_delete(CacheEntry).where(CacheEntry.key == key))
        await db.commit()


async def clear_by_module(db: AsyncSession, module: str) -> int:
    """
    Clear all cache entries for a module.
    - Remove matching keys from in-memory cache
    - Delete matching entries from DB
    - Return count of cleared entries
    """
    # Remove from memory
    keys_to_remove = [k for k, v in _cache_store.items() if v["module"] == module]
    for k in keys_to_remove:
        del _cache_store[k]

    # Remove from DB
    from sqlalchemy import delete as sql_delete
    result = await db.execute(sql_delete(CacheEntry).where(CacheEntry.module == module))
    await db.commit()

    return result.rowcount


async def get_stats(db: AsyncSession, module: str | None = None) -> list[CacheStatsResponse]:
    """
    Get cache statistics.
    - If module specified: return stats for that module
    - If no module: return stats for all modules
    - Calculate from in-memory counters + DB records
    - For each module:
      1. total_hits, total_misses, total_evictions
      2. hit_rate = hits / (hits + misses) * 100 (0 if no hits/misses)
      3. entry_count = number of active cache entries
      4. recent_stats = last 10 DB stats records
    - Return list of CacheStatsResponse
    """
    modules_to_query = [module] if module else list(_stats_counters.keys())

    if not module:
        # Also include modules that have DB entries but no current in-memory stats
        result = await db.execute(select(CacheEntry.module).distinct())
        db_modules = [row[0] for row in result.all()]
        # Python's built-in set has been shadowed by our module-level set function.
        import builtins
        modules_to_query = list(builtins.set(modules_to_query + db_modules))

        # And include modules from historical stats
        result = await db.execute(select(CacheStatsRecord.module).distinct())
        hist_modules = [row[0] for row in result.all()]
        modules_to_query = list(builtins.set(modules_to_query + hist_modules))

    responses = []

    for m in modules_to_query:
        # 1. Total hits, misses, evictions (Memory + historical DB)
        mem_hits = _stats_counters.get(m, {}).get("hits", 0)
        mem_misses = _stats_counters.get(m, {}).get("misses", 0)
        mem_evictions = _stats_counters.get(m, {}).get("evictions", 0)

        hist_result = await db.execute(
            select(
                func.sum(CacheStatsRecord.hits),
                func.sum(CacheStatsRecord.misses),
                func.sum(CacheStatsRecord.evictions)
            ).where(CacheStatsRecord.module == m)
        )
        hist_row = hist_result.first()
        hist_hits = hist_row[0] or 0 if hist_row else 0
        hist_misses = hist_row[1] or 0 if hist_row else 0
        hist_evictions = hist_row[2] or 0 if hist_row else 0

        total_hits = mem_hits + hist_hits
        total_misses = mem_misses + hist_misses
        total_evictions = mem_evictions + hist_evictions

        # 2. Hit rate
        hit_rate = 0.0
        if total_hits + total_misses > 0:
            hit_rate = (total_hits / (total_hits + total_misses)) * 100.0

        # 3. Entry count (active)
        # Using DB count for accuracy (memory might not have everything)
        now = datetime.now()
        count_result = await db.execute(
            select(func.count(CacheEntry.id))
            .where(CacheEntry.module == m, CacheEntry.expires_at > now)
        )
        entry_count = count_result.scalar() or 0

        # 4. Recent stats
        recent_result = await db.execute(
            select(CacheStatsRecord)
            .where(CacheStatsRecord.module == m)
            .order_by(desc(CacheStatsRecord.recorded_at))
            .limit(10)
        )
        recent_records = recent_result.scalars().all()
        recent_stats = [
            CacheStatsRecordResponse(
                id=r.id,
                module=r.module,
                hits=r.hits,
                misses=r.misses,
                evictions=r.evictions,
                recorded_at=r.recorded_at
            ) for r in recent_records
        ]

        responses.append(CacheStatsResponse(
            module=m,
            total_hits=total_hits,
            total_misses=total_misses,
            total_evictions=total_evictions,
            hit_rate=hit_rate,
            entry_count=entry_count,
            recent_stats=recent_stats
        ))

    return responses


async def invalidate_pattern(db: AsyncSession, pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    - Pattern is a prefix: "inventory:*" matches all keys starting with "inventory:"
    - For prefix matching, strip trailing "*" if present
    - Find all keys in in-memory cache matching the prefix
    - Remove matching entries from memory and DB
    - Return count of invalidated entries
    """
    prefix = pattern
    if prefix.endswith("*"):
        prefix = prefix[:-1]

    # Memory
    keys_to_remove = [k for k in _cache_store.keys() if k.startswith(prefix)]
    for k in keys_to_remove:
        del _cache_store[k]

    # DB
    from sqlalchemy import delete as sql_delete
    result = await db.execute(
        sql_delete(CacheEntry).where(CacheEntry.key.startswith(prefix))
    )
    await db.commit()

    return result.rowcount


async def warm_cache(db: AsyncSession, entries: list[CacheEntryCreate]) -> list[CacheEntry]:
    """
    Pre-populate cache with multiple entries.
    - Validate all entries
    - For each entry, call set()
    - Return list of CacheEntry
    """
    results = []
    for entry_data in entries:
        entry = await set(db, entry_data)
        results.append(entry)
    return results


async def cleanup_expired(db: AsyncSession) -> int:
    """
    Background task: remove expired entries from memory and DB.
    - Iterate in-memory cache, remove entries where expires_at < now
    - Delete from DB where expires_at < now
    - Record evictions in stats
    - Return count of cleaned entries
    """
    now = datetime.now()
    cleaned_count = 0

    # Memory
    keys_to_remove = []
    for k, v in _cache_store.items():
        if v["expires_at"] < now:
            keys_to_remove.append(k)

    for k in keys_to_remove:
        module = _cache_store[k]["module"]
        _init_module_stats(module)
        _stats_counters[module]["evictions"] += 1
        del _cache_store[k]
        cleaned_count += 1

    # DB - fetch to get module for stats, then delete
    expired_result = await db.execute(select(CacheEntry).where(CacheEntry.expires_at < now))
    expired_entries = expired_result.scalars().all()

    for entry in expired_entries:
        if entry.key not in keys_to_remove: # Avoid double counting if it was in memory
            _init_module_stats(entry.module)
            _stats_counters[entry.module]["evictions"] += 1
            cleaned_count += 1

    # Actually, we need to re-query with the now value because expired_entries
    # above may not have fetched everything properly or we didn't delete the right things
    from sqlalchemy import delete as sql_delete
    result = await db.execute(sql_delete(CacheEntry).where(CacheEntry.expires_at < now))
    await db.commit()
    # Any rows deleted here that weren't in expired_entries won't be counted in cleaned_count
    # or evictions, but that's a minor stats issue compared to failing to actually delete.

    return cleaned_count


async def flush_stats(db: AsyncSession) -> None:
    """
    Flush in-memory stats counters to DB.
    - For each module in _stats_counters:
      1. Create CacheStatsRecord with current counters
      2. Reset in-memory counters
    """
    now = datetime.now()
    records = []

    for module, counters in _stats_counters.items():
        if counters["hits"] > 0 or counters["misses"] > 0 or counters["evictions"] > 0:
            record = CacheStatsRecord(
                module=module,
                hits=counters["hits"],
                misses=counters["misses"],
                evictions=counters["evictions"],
                recorded_at=now
            )
            records.append(record)

            # Reset
            counters["hits"] = 0
            counters["misses"] = 0
            counters["evictions"] = 0

    if records:
        db.add_all(records)
        await db.commit()


def clear_cache_state() -> None:
    """
    Clear all in-memory cache and stats state.
    Useful for testing.
    """
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
    Sum of len(key) + len(value) for all entries.
    """
    total = 0
    for k, v in _cache_store.items():
        total += len(k)
        if isinstance(v.get("value"), str):
            total += len(v["value"])
    return total


async def start_cleanup_task(db_session_factory, interval_seconds: int = 60) -> None:
    """
    Periodic task that runs cleanup_expired and flush_stats.
    Called from FastAPI lifespan startup.
    Runs in an infinite loop with asyncio.sleep(interval_seconds).
    Should handle exceptions gracefully and continue.
    """
    while True:
        try:
            async for db in db_session_factory():
                await cleanup_expired(db)
                await flush_stats(db)
        except Exception as e:
            logging.error(f"Error in cache cleanup task: {e}")

        await asyncio.sleep(interval_seconds)

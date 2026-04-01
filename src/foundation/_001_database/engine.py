"""
Database engine and session management.

Usage in routers:
    from src.foundation._001_database import get_db

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        ...
"""
from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ── Defaults (overridable via env vars) ──────────────────────

_DEFAULT_URL = "sqlite+aiosqlite:///./erp_ultra.db"
DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_URL)

_echo: bool = os.getenv("SQL_ECHO", "0") == "1"

# ── Module-level singletons ─────────────────────────────────

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=_echo)
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# ── Factory helpers (for testing / multi-db) ─────────────────

def create_engine(url: str, *, echo: bool = False) -> AsyncEngine:
    """Create a new async engine for a given database URL."""
    return create_async_engine(url, echo=echo)


def get_session_factory(
    eng: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Return a session factory bound to *eng* (default: module engine)."""
    target = eng or engine
    return async_sessionmaker(target, class_=AsyncSession, expire_on_commit=False)


# ── FastAPI dependency ───────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and ensure cleanup after the request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

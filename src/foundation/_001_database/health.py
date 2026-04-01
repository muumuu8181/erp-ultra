"""
Database health-check utilities.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import async_session_factory


async def check_db_health() -> dict[str, str]:
    """
    Execute a lightweight query to verify the database is reachable.

    Returns:
        {"status": "ok"} on success, {"status": "error", "detail": ...} on failure.
    """
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}

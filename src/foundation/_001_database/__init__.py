"""
001_database - Database engine, session management, and connection health.

Provides:
- SQLAlchemy async engine factory
- Session factory (async)
- FastAPI dependency `get_db` for injecting DB sessions into routers
- Health-check endpoint for orchestration probes
"""
from src.foundation._001_database.engine import (
    create_engine,
    get_session_factory,
    get_db,
    engine,
    async_session_factory,
)
from src.foundation._001_database.health import check_db_health

__all__ = [
    "create_engine",
    "get_session_factory",
    "get_db",
    "engine",
    "async_session_factory",
    "check_db_health",
]

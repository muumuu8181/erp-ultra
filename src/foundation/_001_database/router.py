"""
Health-check and metadata routes for the database module.
"""
from __future__ import annotations

from fastapi import APIRouter

from src.foundation._001_database.health import check_db_health

router = APIRouter(prefix="/api/v1/database", tags=["database"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return database connectivity status."""
    return await check_db_health()

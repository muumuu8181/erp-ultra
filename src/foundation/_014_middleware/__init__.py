"""
Common Middleware module.

Provides composable middleware for FastAPI applications.
"""

from src.foundation._014_middleware.service import (
    MiddlewareConfig,
    RequestTimingMiddleware,
    RequestIdMiddleware,
    TenantMiddleware,
    add_cors_middleware,
    register_all_middleware,
    get_default_config,
    get_active_middleware,
)
from src.foundation._014_middleware.router import router

__all__ = [
    "MiddlewareConfig",
    "RequestTimingMiddleware",
    "RequestIdMiddleware",
    "TenantMiddleware",
    "add_cors_middleware",
    "register_all_middleware",
    "get_default_config",
    "get_active_middleware",
    "router",
]

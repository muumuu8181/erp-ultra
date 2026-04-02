from fastapi import APIRouter

from src.foundation._014_middleware.schemas import MiddlewareStatusResponse
from src.foundation._014_middleware.service import get_default_config, get_active_middleware

router = APIRouter(prefix="/api/v1/middleware", tags=["middleware"])


@router.get("/config", response_model=MiddlewareStatusResponse)
async def get_middleware_config() -> MiddlewareStatusResponse:
    """Returns current middleware configuration and active middleware."""
    config = get_default_config()
    active_middleware = get_active_middleware(config)
    return MiddlewareStatusResponse(
        middleware=active_middleware,
        config=config,
    )

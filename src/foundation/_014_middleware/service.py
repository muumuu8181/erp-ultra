import os
import time
import uuid
from typing import Optional

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from src.foundation._014_middleware.schemas import MiddlewareConfig


def get_default_config() -> MiddlewareConfig:
    """Build default middleware configuration from environment variables.

    Environment variables (all optional):
    - CORS_ORIGINS: comma-separated list of origins (default: "*")
    - CORS_ALLOW_CREDENTIALS: "true"/"false" (default: "true")
    - TIMING_ENABLED: "true"/"false" (default: "true")
    - REQUEST_ID_ENABLED: "true"/"false" (default: "true")
    - REQUEST_ID_HEADER: header name (default: "X-Request-ID")
    - TENANT_HEADER_NAME: header name (default: "X-Tenant-ID")
    - TENANT_REQUIRED: "true"/"false" (default: "false")

    Returns:
        MiddlewareConfig with values from env vars or defaults.
    """
    cors_origins_env = os.environ.get("CORS_ORIGINS")
    cors_origins = cors_origins_env.split(",") if cors_origins_env else ["*"]

    cors_allow_credentials = os.environ.get("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"
    timing_enabled = os.environ.get("TIMING_ENABLED", "true").lower() == "true"
    request_id_enabled = os.environ.get("REQUEST_ID_ENABLED", "true").lower() == "true"
    request_id_header = os.environ.get("REQUEST_ID_HEADER", "X-Request-ID")
    tenant_header_name = os.environ.get("TENANT_HEADER_NAME", "X-Tenant-ID")
    tenant_required = os.environ.get("TENANT_REQUIRED", "false").lower() == "true"

    return MiddlewareConfig(
        cors_origins=cors_origins,
        cors_allow_credentials=cors_allow_credentials,
        timing_enabled=timing_enabled,
        request_id_enabled=request_id_enabled,
        request_id_header=request_id_header,
        tenant_header_name=tenant_header_name,
        tenant_required=tenant_required,
    )


def get_active_middleware(config: MiddlewareConfig) -> list[str]:
    """Return a list of active middleware names based on configuration.

    Args:
        config: The middleware configuration.
    Returns:
        List of middleware names that are active.
    """
    active = ["CORSMiddleware", "TenantMiddleware"]
    if config.request_id_enabled:
        active.append("RequestIdMiddleware")
    if config.timing_enabled:
        active.append("RequestTimingMiddleware")
    return active


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware that measures request duration and adds X-Response-Time header.

    Measures the total time from when the request enters the middleware
    to when the response is ready. Adds the timing as a header value
    in milliseconds.

    Header format: X-Response-Time: 123.45ms

    Usage:
        app.add_middleware(RequestTimingMiddleware)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Measure request duration and add timing header.

        Steps:
        1. Record start time using time.perf_counter()
        2. Call next middleware/endpoint
        3. Calculate elapsed time in milliseconds
        4. Add X-Response-Time header to response (format: "{ms:.2f}ms")
        5. Return response
        """
        start_time = time.perf_counter()
        response = await call_next(request)
        elapsed_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Response-Time"] = f"{elapsed_time:.2f}ms"
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that generates a unique request ID and adds X-Request-ID header.

    If the incoming request already has an X-Request-ID header, uses that value.
    Otherwise, generates a new UUID4.

    The request ID is stored in request.state.request_id for downstream access.

    Header: X-Request-ID: <uuid4-string>

    Usage:
        app.add_middleware(RequestIdMiddleware, header_name="X-Request-ID")
    """

    def __init__(self, app, header_name: str = "X-Request-ID"):
        """Initialize with configurable header name.

        Args:
            app: The ASGI application.
            header_name: Name of the header for request ID (default: "X-Request-ID").
        """
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next) -> Response:
        """Generate or propagate request ID.

        Steps:
        1. Check if request already has the header (case-insensitive)
        2. If present, use existing value; otherwise generate UUID4
        3. Store in request.state.request_id
        4. Call next middleware/endpoint
        5. Add X-Request-ID header to response
        6. Return response
        """
        request_id = request.headers.get(self.header_name)
        if not request_id:
            request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response


def add_cors_middleware(app: FastAPI, config: MiddlewareConfig) -> None:
    """Add Starlette CORS middleware with the given configuration.

    Uses Starlette's built-in CORSMiddleware with configuration from
    MiddlewareConfig. In development (ENV != production), defaults to
    allow all origins. In production, uses explicitly configured origins.

    Args:
        app: The FastAPI application.
        config: MiddlewareConfig with CORS settings.
    """
    app.add_middleware(
        StarletteCORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=config.cors_allow_methods,
        allow_headers=config.cors_allow_headers,
    )


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts tenant_id from a request header for multi-tenant support.

    Reads the tenant ID from a configurable header (default: X-Tenant-ID).
    Stores the tenant ID in request.state.tenant_id for downstream access.

    If tenant_required is True and the header is missing, returns 400 error.

    Usage:
        app.add_middleware(TenantMiddleware, header_name="X-Tenant-ID", required=False)
    """

    def __init__(self, app, header_name: str = "X-Tenant-ID", required: bool = False):
        """Initialize with configurable header name and required flag.

        Args:
            app: The ASGI application.
            header_name: Name of the header containing tenant ID (default: "X-Tenant-ID").
            required: Whether tenant ID header is required (default: False).
        """
        super().__init__(app)
        self.header_name = header_name
        self.required = required

    async def dispatch(self, request: Request, call_next) -> Response:
        """Extract tenant ID from header.

        Steps:
        1. Read tenant_id from configured header
        2. If required and missing, return 400 JSON error response
        3. Store in request.state.tenant_id (None if not provided and not required)
        4. Call next middleware/endpoint
        5. Return response
        """
        tenant_id = request.headers.get(self.header_name)
        if self.required and not tenant_id:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Missing required header: {self.header_name}"}
            )

        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response


def register_all_middleware(app: FastAPI, config: Optional[MiddlewareConfig] = None) -> None:
    """Register all middleware on a FastAPI application in the correct order.

    Order matters - middleware executes in reverse order of addition:
    1. CORS (outermost - handles preflight first)
    2. TenantMiddleware
    3. RequestIdMiddleware
    4. RequestTimingMiddleware (innermost - closest to the route handler)

    Args:
        app: The FastAPI application instance.
        config: Optional MiddlewareConfig. Uses defaults if not provided.
    """
    if config is None:
        config = get_default_config()

    if config.timing_enabled:
        app.add_middleware(RequestTimingMiddleware)

    if config.request_id_enabled:
        app.add_middleware(RequestIdMiddleware, header_name=config.request_id_header)

    app.add_middleware(
        TenantMiddleware,
        header_name=config.tenant_header_name,
        required=config.tenant_required
    )

    add_cors_middleware(app, config)

import os
import uuid
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.foundation._014_middleware.schemas import MiddlewareConfig
from src.foundation._014_middleware.service import (
    get_default_config,
    get_active_middleware,
    RequestTimingMiddleware,
    RequestIdMiddleware,
    TenantMiddleware,
    add_cors_middleware,
    register_all_middleware,
)


def test_get_default_config(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ALLOW_CREDENTIALS", raising=False)
    monkeypatch.delenv("TIMING_ENABLED", raising=False)
    monkeypatch.delenv("REQUEST_ID_ENABLED", raising=False)
    monkeypatch.delenv("REQUEST_ID_HEADER", raising=False)
    monkeypatch.delenv("TENANT_HEADER_NAME", raising=False)
    monkeypatch.delenv("TENANT_REQUIRED", raising=False)

    config = get_default_config()
    assert config.cors_origins == ["*"]
    assert config.cors_allow_credentials is False
    assert config.timing_enabled is True
    assert config.request_id_enabled is True
    assert config.request_id_header == "X-Request-ID"
    assert config.tenant_header_name == "X-Tenant-ID"
    assert config.tenant_required is False


def test_get_default_config_env_vars(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
    monkeypatch.setenv("CORS_ALLOW_CREDENTIALS", "false")
    monkeypatch.setenv("TIMING_ENABLED", "false")
    monkeypatch.setenv("REQUEST_ID_ENABLED", "false")
    monkeypatch.setenv("REQUEST_ID_HEADER", "X-Custom-ID")
    monkeypatch.setenv("TENANT_HEADER_NAME", "X-Org-ID")
    monkeypatch.setenv("TENANT_REQUIRED", "true")

    config = get_default_config()
    assert config.cors_origins == ["http://localhost:3000", "http://localhost:8080"]
    assert config.cors_allow_credentials is False
    assert config.timing_enabled is False
    assert config.request_id_enabled is False
    assert config.request_id_header == "X-Custom-ID"
    assert config.tenant_header_name == "X-Org-ID"
    assert config.tenant_required is True


def test_get_active_middleware():
    config = MiddlewareConfig()
    active = get_active_middleware(config)
    assert "CORSMiddleware" in active
    assert "TenantMiddleware" in active
    assert "RequestIdMiddleware" in active
    assert "RequestTimingMiddleware" in active

    config.timing_enabled = False
    config.request_id_enabled = False
    active = get_active_middleware(config)
    assert "CORSMiddleware" in active
    assert "TenantMiddleware" in active
    assert "RequestIdMiddleware" not in active
    assert "RequestTimingMiddleware" not in active


@pytest.mark.asyncio
async def test_request_timing_middleware():
    app = FastAPI()
    app.add_middleware(RequestTimingMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/test")

    assert response.status_code == 200
    assert "X-Response-Time" in response.headers
    assert response.headers["X-Response-Time"].endswith("ms")

    time_val = float(response.headers["X-Response-Time"].replace("ms", ""))
    assert time_val >= 0


@pytest.mark.asyncio
async def test_request_id_middleware_generates_id():
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    request_id_in_handler = None

    @app.get("/test")
    async def test_endpoint(request: Request):
        nonlocal request_id_in_handler
        request_id_in_handler = request.state.request_id
        return {"status": "ok"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/test")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == request_id_in_handler

    # Check if it's a valid UUID
    uuid.UUID(response.headers["X-Request-ID"])


@pytest.mark.asyncio
async def test_request_id_middleware_preserves_id():
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"status": "ok"}

    custom_id = "custom-id-123"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/test", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == custom_id


@pytest.mark.asyncio
async def test_tenant_middleware_not_required():
    app = FastAPI()
    app.add_middleware(TenantMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"tenant_id": getattr(request.state, "tenant_id", None)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/test")

    assert response.status_code == 200
    assert response.json() == {"tenant_id": None}


@pytest.mark.asyncio
async def test_tenant_middleware_required_missing():
    app = FastAPI()
    app.add_middleware(TenantMiddleware, required=True)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"status": "ok"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/test")

    assert response.status_code == 400
    assert response.json() == {"detail": "Missing required header: X-Tenant-ID"}


@pytest.mark.asyncio
async def test_tenant_middleware_with_header():
    app = FastAPI()
    app.add_middleware(TenantMiddleware, required=True)

    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"tenant_id": request.state.tenant_id}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/test", headers={"X-Tenant-ID": "tenant-456"})

    assert response.status_code == 200
    assert response.json() == {"tenant_id": "tenant-456"}


def test_register_all_middleware():
    app = FastAPI()
    # This should not raise an exception (especially the Starlette CORS assertion)
    register_all_middleware(app)

    # Check that middleware were actually added
    # Starlette stores middleware in app.user_middleware
    assert len(app.user_middleware) > 0


@pytest.mark.asyncio
async def test_cors_middleware():
    app = FastAPI()
    config = MiddlewareConfig(cors_origins=["http://example.com"])
    add_cors_middleware(app, config)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.options("/test", headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET"
        })

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://example.com"

"""
Tests for the error router and exception handler integration.
"""

import pytest
import httpx
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from shared.errors import (
    ERPError,
    ValidationError,
    NotFoundError,
    DuplicateError,
    BusinessRuleError,
    AuthorizationError,
    ConcurrentModificationError,
    IntegrationError,
    CalculationError,
)
from src.foundation._013_errors.router import router
from src.foundation._013_errors.service import register_exception_handlers

# Setup test app
app = FastAPI()
app.include_router(router)
register_exception_handlers(app)

# Test routes that raise specific errors
@app.get("/test/validation")
async def raise_validation():
    raise ValidationError("Invalid input", field="email")

@app.get("/test/not-found")
async def raise_not_found():
    raise NotFoundError("Customer", "CUST-001")

@app.get("/test/duplicate")
async def raise_duplicate():
    raise DuplicateError("Customer", "CUST-001")

@app.get("/test/business-rule")
async def raise_business_rule():
    raise BusinessRuleError("Cannot delete", rule="no_open_orders")

@app.get("/test/authorization")
async def raise_authorization():
    raise AuthorizationError("delete", "customer")

@app.get("/test/concurrent")
async def raise_concurrent():
    raise ConcurrentModificationError("order")

@app.get("/test/integration")
async def raise_integration():
    raise IntegrationError("BankAPI", "timeout")

@app.get("/test/calculation")
async def raise_calculation():
    raise CalculationError("invalid rate")

@app.get("/test/erp-error")
async def raise_erp_error():
    raise ERPError("generic erp error")

@app.get("/test/exception")
async def raise_exception():
    raise Exception("unhandled test exception")


@pytest.mark.asyncio
async def test_get_error_codes():
    """Test GET /api/v1/errors/codes returns 200 with correct structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/errors/codes")

    assert response.status_code == 200
    data = response.json()
    assert "codes" in data
    assert "total" in data
    assert len(data["codes"]) > 0
    assert data["total"] == len(data["codes"])

@pytest.mark.asyncio
async def test_raise_validation_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/validation")

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert data["details"]["field"] == "email"
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers

@pytest.mark.asyncio
async def test_raise_not_found_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/not-found")

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "NOT_FOUND"

@pytest.mark.asyncio
async def test_raise_duplicate_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/duplicate")

    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "DUPLICATE"

@pytest.mark.asyncio
async def test_raise_business_rule_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/business-rule")

    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "BUSINESS_RULE"
    assert data["details"]["rule"] == "no_open_orders"

@pytest.mark.asyncio
async def test_raise_authorization_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/authorization")

    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "AUTHORIZATION_ERROR"

@pytest.mark.asyncio
async def test_raise_concurrent_modification_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/concurrent")

    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "CONCURRENT_MODIFICATION"
    assert data["details"]["retry"] is True

@pytest.mark.asyncio
async def test_raise_integration_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/integration")

    assert response.status_code == 502
    data = response.json()
    assert data["code"] == "INTEGRATION_ERROR"

@pytest.mark.asyncio
async def test_raise_calculation_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/calculation")

    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "CALCULATION_ERROR"

@pytest.mark.asyncio
async def test_raise_erp_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/erp-error")

    assert response.status_code == 500
    data = response.json()
    assert data["code"] == "ERP_ERROR"

@pytest.mark.asyncio
async def test_raise_unhandled_exception():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/exception")

    assert response.status_code == 500
    data = response.json()
    assert data["code"] == "INTERNAL_ERROR"
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers

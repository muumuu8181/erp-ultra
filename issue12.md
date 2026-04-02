## Overview

Implement the Global Error Handler Middleware module. This module provides FastAPI exception handlers for all error types defined in `shared.errors`, a global middleware that catches all exceptions and returns structured JSON responses, request ID generation/propagation, and an endpoint to list all error codes.

## Directory to Create

```
src/foundation/_013_errors/
├── __init__.py
├── models.py          # Empty (middleware module, no DB models)
├── schemas.py
├── service.py
├── router.py
├── validators.py      # Minimal (middleware module)
├── README.md
└── tests/
    ├── __init__.py
    ├── test_models.py      # Minimal
    ├── test_service.py
    ├── test_router.py
    └── test_validators.py  # Minimal
```

## Key Rules

- All directories use underscore prefix: `_013_errors`
- Import SQLAlchemy Base from `shared.types`: `from shared.types import Base, BaseModel`
- Import Pydantic schemas from `shared.types`: `from shared.types import BaseSchema, PaginatedResponse`
- Import errors from `shared.errors`: `from shared.errors import NotFoundError, ValidationError, DuplicateError, BusinessRuleError, AuthorizationError, ConcurrentModificationError, IntegrationError, CalculationError, ERPError`
- Import schema constants from `shared.schema`: `from shared.schema import ColLen, Precision`
- DB sessions come from `src.foundation._001_database.engine`: `from src.foundation._001_database.engine import get_db`
- All public functions must have type hints and docstrings
- Router prefix pattern: `/api/v1/errors`
- Tests use pytest-asyncio
- This module is INDEPENDENT - only import from `shared/` and `src.foundation._001_database`
- **No database models** - this is a middleware module

## Models (`models.py`)

This file should exist but contain only a docstring:
```python
"""
No database models for the error handler module.
This module provides middleware and exception handlers, not data persistence.
"""
```

## Schemas (`schemas.py`)

```python
from shared.types import BaseSchema
from pydantic import Field
from datetime import datetime
from typing import Optional, Any

class ErrorResponse(BaseSchema):
    """Standard error response returned for all error types."""
    code: str = Field(..., description="Machine-readable error code (e.g. VALIDATION_ERROR)")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")

class ErrorCodeInfo(BaseSchema):
    """Information about a single error code."""
    code: str = Field(..., description="Error code string")
    http_status: int = Field(..., description="HTTP status code mapped to this error")
    description: str = Field(..., description="Human-readable description of when this error occurs")
    example_message: str = Field(..., description="Example error message")

class ErrorCodesResponse(BaseSchema):
    """Response listing all error codes."""
    codes: list[ErrorCodeInfo] = Field(..., description="List of all error codes")
    total: int = Field(..., description="Total number of error codes")
```

## Service (`service.py`) - CORE FILE

### Error Code Mapping

```python
from shared.errors import (
    ERPError, ValidationError, NotFoundError, DuplicateError,
    BusinessRuleError, AuthorizationError, ConcurrentModificationError,
    IntegrationError, CalculationError
)

# Mapping of error types to HTTP status codes
ERROR_STATUS_MAP: dict[type[ERPError], int] = {
    ValidationError: 400,
    CalculationError: 400,
    NotFoundError: 404,
    DuplicateError: 409,
    ConcurrentModificationError: 409,
    BusinessRuleError: 422,
    AuthorizationError: 403,
    IntegrationError: 502,
}

def get_http_status(error: ERPError) -> int:
    """Map an ERPError subclass to its HTTP status code.

    Walks the MRO of the error class to find the most specific match
    in ERROR_STATUS_MAP. Falls back to 500 for base ERPError.

    Args:
        error: An ERPError instance.
    Returns:
        The corresponding HTTP status code.
    """

def build_error_response(error: Exception, request_id: Optional[str] = None) -> dict:
    """Build a standardized error response dict from any exception.

    For ERPError subclasses:
    - Uses the error's code, message, and details
    - Maps to the correct HTTP status code

    For unhandled exceptions:
    - Returns code "INTERNAL_ERROR"
    - In production (ENV=production): sanitized message "An internal error occurred"
    - In development: includes the actual exception message
    - No stack trace in any environment

    Args:
        error: The exception that occurred.
        request_id: Optional request ID for tracing.
    Returns:
        Dict with keys: code, message, details, timestamp, request_id.
    """

def get_error_codes() -> list[dict[str, Any]]:
    """Return a list of all error codes with their HTTP status, description, and example.

    Returns:
        List of dicts, each with: code, http_status, description, example_message.
        Covers all error types in shared.errors.
    """

def generate_request_id() -> str:
    """Generate a unique request ID using UUID4.

    Returns:
        A UUID4 string in the format "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx".
    """
```

### Error Code Reference

The service must provide the following error code reference:

| Error Class | Code | HTTP Status | Description | Example Message |
|-------------|------|-------------|-------------|-----------------|
| `ValidationError` | `VALIDATION_ERROR` | 400 | Input validation failed | "Invalid email format for field: email" |
| `CalculationError` | `CALCULATION_ERROR` | 400 | Calculation error (tax, depreciation, etc) | "Tax calculation failed: invalid rate" |
| `AuthorizationError` | `AUTHORIZATION_ERROR` | 403 | User lacks permission | "Not authorized to delete on customer" |
| `NotFoundError` | `NOT_FOUND` | 404 | Requested resource not found | "Customer not found: CUST-001" |
| `DuplicateError` | `DUPLICATE` | 409 | Resource already exists | "Customer already exists: CUST-001" |
| `ConcurrentModificationError` | `CONCURRENT_MODIFICATION` | 409 | Optimistic locking conflict | "Concurrent modification detected on order" |
| `BusinessRuleError` | `BUSINESS_RULE` | 422 | Business rule violation | "Cannot delete customer with open orders" |
| `IntegrationError` | `INTEGRATION_ERROR` | 502 | External system failure | "[BankAPI] Connection timeout" |
| `ERPError` (base) | `ERP_ERROR` | 500 | Generic ERP error | "An unexpected error occurred" |

### Exception Handlers for FastAPI

Create functions that can be registered as FastAPI exception handlers:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError -> 400 with field info.

    Returns JSON with code="VALIDATION_ERROR", message, details containing "field" key.
    """

async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError -> 404."""

async def duplicate_error_handler(request: Request, exc: DuplicateError) -> JSONResponse:
    """Handle DuplicateError -> 409."""

async def business_rule_error_handler(request: Request, exc: BusinessRuleError) -> JSONResponse:
    """Handle BusinessRuleError -> 422 with rule info."""

async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle AuthorizationError -> 403."""

async def concurrent_modification_error_handler(request: Request, exc: ConcurrentModificationError) -> JSONResponse:
    """Handle ConcurrentModificationError -> 409 with retry hint.

    Includes "retry" in details: {"retry": True, "message": "Please retry the operation"}
    """

async def integration_error_handler(request: Request, exc: IntegrationError) -> JSONResponse:
    """Handle IntegrationError -> 502."""

async def calculation_error_handler(request: Request, exc: CalculationError) -> JSONResponse:
    """Handle CalculationError -> 400."""

async def erp_error_handler(request: Request, exc: ERPError) -> JSONResponse:
    """Handle generic ERPError -> 500."""

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions -> 500.

    Behavior:
    - Returns code="INTERNAL_ERROR"
    - In production: message="An internal error occurred" (sanitized, no details leaked)
    - In development (ENV != production): message includes actual exception string
    - Never includes stack trace
    - Includes request_id from request state if available
    """
```

### Global Exception Handler Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class GlobalExceptionHandler(BaseHTTPMiddleware):
    """Middleware that catches all unhandled exceptions and returns structured JSON.

    This middleware wraps the entire request processing pipeline. If any exception
    occurs during request processing that is not caught by FastAPI exception handlers,
    this middleware catches it and returns a structured ErrorResponse.

    It also generates a request_id (UUID4) and stores it in request.state.request_id
    so that downstream handlers and exception handlers can include it in responses.

    Usage:
        app = FastAPI()
        app.add_middleware(GlobalExceptionHandler)
    """

    async def dispatch(self, request: Request, call_next):
        """Process request with global error handling.

        Steps:
        1. Generate request_id (UUID4) and store in request.state.request_id
        2. Call the next middleware/endpoint
        3. If successful, add X-Request-ID header to response
        4. If exception occurs:
           a. Build error response using build_error_response()
           b. Return JSONResponse with appropriate status code
           c. Include X-Request-ID header
        """
```

### Registration Helper

```python
def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on a FastAPI application.

    Registers handlers for all ERPError subclasses and the catch-all.
    Also adds the GlobalExceptionHandler middleware.

    Args:
        app: The FastAPI application instance.
    """
```

## Router (`router.py`)

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/errors", tags=["error-handler"])
```

### Endpoints

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| GET | `/errors/codes` | List all error codes with descriptions | None | `ErrorCodesResponse` |

## Validators (`validators.py`)

Minimal validators:
```python
"""
Minimal validators for the error handler module.
Most validation is done by the exception handlers themselves.
"""
```

## Test Requirements (`tests/`)

All tests use pytest-asyncio.

### `test_service.py` - MAIN TEST FILE

- Test `get_http_status` for each error type returns correct status code
- Test `get_http_status` for unknown ERPError subclass returns 500
- Test `build_error_response` with ValidationError includes field in details
- Test `build_error_response` with NotFoundError returns 404 status
- Test `build_error_response` with DuplicateError returns 409 status
- Test `build_error_response` with BusinessRuleError includes rule info
- Test `build_error_response` with AuthorizationError returns 403 status
- Test `build_error_response` with ConcurrentModificationError includes retry hint
- Test `build_error_response` with IntegrationError returns 502 status
- Test `build_error_response` with CalculationError returns 400 status
- Test `build_error_response` with generic ERPError returns 500 status
- Test `build_error_response` with unhandled Exception in production mode: sanitized message
- Test `build_error_response` with unhandled Exception in development mode: actual message
- Test `build_error_response` includes request_id when provided
- Test `build_error_response` includes timestamp
- Test `get_error_codes` returns all error codes
- Test `get_error_codes` each entry has code, http_status, description, example_message
- Test `generate_request_id` returns valid UUID4 format

### `test_router.py`

- Use `httpx.AsyncClient` with `ASGITransport`
- Create a `FastAPI` app fixture that includes the error router AND registers exception handlers
- Test GET `/api/v1/errors/codes` returns 200 with list of error codes
- Test GET `/api/v1/errors/codes` response has correct structure (codes list, total)

### Exception Handler Integration Tests (in `test_router.py` or separate)

Create test routes that deliberately raise each error type, then verify the middleware returns correct responses:

```python
# Create a test app with routes that raise errors
from fastapi import FastAPI
from shared.errors import *

test_app = FastAPI()

@test_app.get("/test/validation")
async def raise_validation():
    raise ValidationError("Invalid input", field="email")

@test_app.get("/test/not-found")
async def raise_not_found():
    raise NotFoundError("Customer", "CUST-001")

# ... etc for each error type

register_exception_handlers(test_app)
```

- Test raising ValidationError returns 400 with code="VALIDATION_ERROR"
- Test raising NotFoundError returns 404 with code="NOT_FOUND"
- Test raising DuplicateError returns 409 with code="DUPLICATE"
- Test raising BusinessRuleError returns 422 with code="BUSINESS_RULE"
- Test raising AuthorizationError returns 403 with code="AUTHORIZATION_ERROR"
- Test raising ConcurrentModificationError returns 409 with "retry" in details
- Test raising IntegrationError returns 502 with code="INTEGRATION_ERROR"
- Test raising CalculationError returns 400 with code="CALCULATION_ERROR"
- Test raising generic ERPError returns 500
- Test raising generic Exception returns 500 with code="INTERNAL_ERROR"
- Test response includes X-Request-ID header
- Test response includes timestamp

### `test_models.py`
- Minimal: verify module imports correctly

### `test_validators.py`
- Minimal: verify module imports correctly

## Dependencies

Only import from these locations:
- `shared.types` -> `Base, BaseModel, BaseSchema`
- `shared.errors` -> `ERPError, ValidationError, NotFoundError, DuplicateError, BusinessRuleError, AuthorizationError, ConcurrentModificationError, IntegrationError, CalculationError`
- `shared.schema` -> `ColLen, Precision`
- Standard library: `uuid, os, datetime, typing, logging`
- Third-party: `fastapi`, `starlette`, `pydantic`, `pytest`, `httpx`

## Quality Checklist

- [ ] All files have module-level docstrings
- [ ] All public functions have type hints and docstrings
- [ ] No database models (middleware module)
- [ ] Schemas inherit from `BaseSchema` with `Config: from_attributes = True`
- [ ] Router uses prefix `/api/v1/errors`
- [ ] All 9 error types have corresponding exception handlers
- [ ] GlobalExceptionHandler middleware catches unhandled exceptions
- [ ] Production mode sanitizes error messages (no stack trace)
- [ ] ConcurrentModificationError response includes retry hint
- [ ] Request ID generated and propagated in X-Request-ID header
- [ ] `register_exception_handlers()` helper for easy app setup
- [ ] Tests pass with `pytest -x src/foundation/_013_errors/tests/`
- [ ] No imports from other foundation modules (only `shared/`)
- [ ] `__init__.py` exports all public symbols

"""
Service layer for the error handler module.
Provides error code mapping, response building, and exception handlers.
"""

import os
import uuid
import logging
from typing import Optional, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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

logger = logging.getLogger(__name__)

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
    for cls in error.__class__.__mro__:
        if cls in ERROR_STATUS_MAP:
            return ERROR_STATUS_MAP[cls]
    return 500


def build_error_response(error: Exception, request_id: Optional[str] = None) -> dict[str, Any]:
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
    from datetime import datetime

    env = os.getenv("ENV", "development")
    response_dict = {
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "details": {},
    }

    if isinstance(error, ERPError):
        response_dict["code"] = error.code
        response_dict["message"] = error.message

        # Merge details safely
        details = {}
        if error.details:
            details.update(error.details)

        # Add specific details for certain errors
        if isinstance(error, ValidationError) and hasattr(error, 'field') and error.field:
            details["field"] = error.field
        elif isinstance(error, ConcurrentModificationError):
            details["retry"] = True
            details["message"] = "Please retry the operation"
        elif isinstance(error, BusinessRuleError) and hasattr(error, 'rule') and error.rule:
            details["rule"] = error.rule

        response_dict["details"] = details
    else:
        response_dict["code"] = "INTERNAL_ERROR"
        if env == "production":
            response_dict["message"] = "An internal error occurred"
        else:
            response_dict["message"] = str(error)

    return response_dict


def get_error_codes() -> list[dict[str, Any]]:
    """Return a list of all error codes with their HTTP status, description, and example.

    Returns:
        List of dicts, each with: code, http_status, description, example_message.
        Covers all error types in shared.errors.
    """
    return [
        {
            "code": "VALIDATION_ERROR",
            "http_status": 400,
            "description": "Input validation failed",
            "example_message": "Invalid email format for field: email",
        },
        {
            "code": "CALCULATION_ERROR",
            "http_status": 400,
            "description": "Calculation error (tax, depreciation, etc)",
            "example_message": "Tax calculation failed: invalid rate",
        },
        {
            "code": "AUTHORIZATION_ERROR",
            "http_status": 403,
            "description": "User lacks permission",
            "example_message": "Not authorized to delete on customer",
        },
        {
            "code": "NOT_FOUND",
            "http_status": 404,
            "description": "Requested resource not found",
            "example_message": "Customer not found: CUST-001",
        },
        {
            "code": "DUPLICATE",
            "http_status": 409,
            "description": "Resource already exists",
            "example_message": "Customer already exists: CUST-001",
        },
        {
            "code": "CONCURRENT_MODIFICATION",
            "http_status": 409,
            "description": "Optimistic locking conflict",
            "example_message": "Concurrent modification detected on order",
        },
        {
            "code": "BUSINESS_RULE",
            "http_status": 422,
            "description": "Business rule violation",
            "example_message": "Cannot delete customer with open orders",
        },
        {
            "code": "INTEGRATION_ERROR",
            "http_status": 502,
            "description": "External system failure",
            "example_message": "[BankAPI] Connection timeout",
        },
        {
            "code": "ERP_ERROR",
            "http_status": 500,
            "description": "Generic ERP error",
            "example_message": "An unexpected error occurred",
        },
    ]


def generate_request_id() -> str:
    """Generate a unique request ID using UUID4.

    Returns:
        A UUID4 string in the format "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx".
    """
    return str(uuid.uuid4())


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError -> 400 with field info.

    Returns JSON with code="VALIDATION_ERROR", message, details containing "field" key.
    """
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError -> 404."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def duplicate_error_handler(request: Request, exc: DuplicateError) -> JSONResponse:
    """Handle DuplicateError -> 409."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def business_rule_error_handler(request: Request, exc: BusinessRuleError) -> JSONResponse:
    """Handle BusinessRuleError -> 422 with rule info."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle AuthorizationError -> 403."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def concurrent_modification_error_handler(request: Request, exc: ConcurrentModificationError) -> JSONResponse:
    """Handle ConcurrentModificationError -> 409 with retry hint.

    Includes "retry" in details: {"retry": True, "message": "Please retry the operation"}
    """
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def integration_error_handler(request: Request, exc: IntegrationError) -> JSONResponse:
    """Handle IntegrationError -> 502."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def calculation_error_handler(request: Request, exc: CalculationError) -> JSONResponse:
    """Handle CalculationError -> 400."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def erp_error_handler(request: Request, exc: ERPError) -> JSONResponse:
    """Handle generic ERPError -> 500."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=get_http_status(exc),
        content=build_error_response(exc, request_id),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions -> 500.

    Behavior:
    - Returns code="INTERNAL_ERROR"
    - In production: message="An internal error occurred" (sanitized, no details leaked)
    - In development (ENV != production): message includes actual exception string
    - Never includes stack trace
    - Includes request_id from request state if available
    """
    logger.exception("Unhandled exception occurred")
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=500,
        content=build_error_response(exc, request_id),
    )


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
        request_id = generate_request_id()
        request.state.request_id = request_id
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            # Re-raise to let FastAPI's exception handlers handle it if they exist
            # For unhandled ones, our unhandled_exception_handler will catch it
            # But the middleware approach in FastAPI might not trigger app handlers
            # if we catch here, so we only return JSONResponse directly if it's completely unhandled
            # Actually, standard practice for FastAPI middleware is to let handlers do their job,
            # but the prompt says "If any exception occurs... this middleware catches it".
            # To avoid bypassing FastAPI handlers for ERPError, we should catch everything here.

            # Wait, the prompt states:
            # "If any exception occurs during request processing that is not caught by FastAPI exception handlers,
            # this middleware catches it and returns a structured ErrorResponse."
            # FastAPI exception handlers run *inside* the middleware stack. So if an exception propagates out
            # of `await call_next(request)`, it means FastAPI didn't handle it.

            status_code = 500
            if isinstance(exc, ERPError):
                status_code = get_http_status(exc)

            error_response = build_error_response(exc, request_id)
            return JSONResponse(
                status_code=status_code,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on a FastAPI application.

    Registers handlers for all ERPError subclasses and the catch-all.
    Also adds the GlobalExceptionHandler middleware.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(DuplicateError, duplicate_error_handler)
    app.add_exception_handler(BusinessRuleError, business_rule_error_handler)
    app.add_exception_handler(AuthorizationError, authorization_error_handler)
    app.add_exception_handler(ConcurrentModificationError, concurrent_modification_error_handler)
    app.add_exception_handler(IntegrationError, integration_error_handler)
    app.add_exception_handler(CalculationError, calculation_error_handler)
    app.add_exception_handler(ERPError, erp_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.add_middleware(GlobalExceptionHandler)

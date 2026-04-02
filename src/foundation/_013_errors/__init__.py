"""
Global Error Handler Middleware Module
Provides exception handling and global middleware for standard error responses.
"""

from .schemas import ErrorResponse, ErrorCodeInfo, ErrorCodesResponse
from .service import (
    get_http_status,
    build_error_response,
    get_error_codes,
    generate_request_id,
    GlobalExceptionHandler,
    register_exception_handlers,
    validation_error_handler,
    not_found_error_handler,
    duplicate_error_handler,
    business_rule_error_handler,
    authorization_error_handler,
    concurrent_modification_error_handler,
    integration_error_handler,
    calculation_error_handler,
    erp_error_handler,
    unhandled_exception_handler,
)
from .router import router

__all__ = [
    "ErrorResponse",
    "ErrorCodeInfo",
    "ErrorCodesResponse",
    "get_http_status",
    "build_error_response",
    "get_error_codes",
    "generate_request_id",
    "GlobalExceptionHandler",
    "register_exception_handlers",
    "validation_error_handler",
    "not_found_error_handler",
    "duplicate_error_handler",
    "business_rule_error_handler",
    "authorization_error_handler",
    "concurrent_modification_error_handler",
    "integration_error_handler",
    "calculation_error_handler",
    "erp_error_handler",
    "unhandled_exception_handler",
    "router",
]

"""
Tests for the error service module.
"""

import os
import uuid
import pytest
from unittest.mock import patch

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
from src.foundation._013_errors.service import (
    get_http_status,
    build_error_response,
    get_error_codes,
    generate_request_id,
)

# Test custom subclass of ERPError
class CustomUnknownError(ERPError):
    pass

def test_get_http_status_known_errors():
    """Test get_http_status returns correct status code for known errors."""
    assert get_http_status(ValidationError("msg", "field")) == 400
    assert get_http_status(CalculationError("msg")) == 400
    assert get_http_status(NotFoundError("res", "id")) == 404
    assert get_http_status(DuplicateError("res", "key")) == 409
    assert get_http_status(ConcurrentModificationError("res")) == 409
    assert get_http_status(BusinessRuleError("msg", "rule")) == 422
    assert get_http_status(AuthorizationError("action", "res")) == 403
    assert get_http_status(IntegrationError("sys", "msg")) == 502

def test_get_http_status_unknown_errors():
    """Test get_http_status returns 500 for unknown ERPError subclass."""
    assert get_http_status(CustomUnknownError("msg")) == 500
    assert get_http_status(ERPError("msg")) == 500

def test_build_error_response_validation_error():
    """Test build_error_response with ValidationError includes field in details."""
    err = ValidationError("msg", "email")
    resp = build_error_response(err)
    assert resp["code"] == "VALIDATION_ERROR"
    assert resp["details"]["field"] == "email"

def test_build_error_response_not_found_error():
    """Test build_error_response with NotFoundError."""
    err = NotFoundError("res", "id")
    resp = build_error_response(err)
    assert resp["code"] == "NOT_FOUND"

def test_build_error_response_duplicate_error():
    """Test build_error_response with DuplicateError."""
    err = DuplicateError("res", "key")
    resp = build_error_response(err)
    assert resp["code"] == "DUPLICATE"

def test_build_error_response_business_rule_error():
    """Test build_error_response with BusinessRuleError includes rule info."""
    err = BusinessRuleError("msg", "my-rule")
    resp = build_error_response(err)
    assert resp["code"] == "BUSINESS_RULE"
    assert resp["details"]["rule"] == "my-rule"

def test_build_error_response_authorization_error():
    """Test build_error_response with AuthorizationError."""
    err = AuthorizationError("action", "res")
    resp = build_error_response(err)
    assert resp["code"] == "AUTHORIZATION_ERROR"

def test_build_error_response_concurrent_modification_error():
    """Test build_error_response with ConcurrentModificationError includes retry hint."""
    err = ConcurrentModificationError("res")
    resp = build_error_response(err)
    assert resp["code"] == "CONCURRENT_MODIFICATION"
    assert resp["details"]["retry"] is True
    assert "Please retry" in resp["details"]["message"]

def test_build_error_response_integration_error():
    """Test build_error_response with IntegrationError."""
    err = IntegrationError("sys", "msg")
    resp = build_error_response(err)
    assert resp["code"] == "INTEGRATION_ERROR"

def test_build_error_response_calculation_error():
    """Test build_error_response with CalculationError."""
    err = CalculationError("msg")
    resp = build_error_response(err)
    assert resp["code"] == "CALCULATION_ERROR"

def test_build_error_response_erp_error():
    """Test build_error_response with generic ERPError."""
    err = ERPError("msg")
    resp = build_error_response(err)
    assert resp["code"] == "ERP_ERROR"

@patch.dict(os.environ, {"ENV": "production"})
def test_build_error_response_unhandled_exception_production():
    """Test build_error_response with unhandled Exception in production mode."""
    err = ValueError("secret DB error")
    resp = build_error_response(err)
    assert resp["code"] == "INTERNAL_ERROR"
    assert resp["message"] == "An internal error occurred"
    assert "secret DB error" not in str(resp)

@patch.dict(os.environ, {"ENV": "development"})
def test_build_error_response_unhandled_exception_development():
    """Test build_error_response with unhandled Exception in development mode."""
    err = ValueError("secret DB error")
    resp = build_error_response(err)
    assert resp["code"] == "INTERNAL_ERROR"
    assert resp["message"] == "secret DB error"

def test_build_error_response_includes_request_id():
    """Test build_error_response includes request_id when provided."""
    req_id = "test-req-id"
    err = ValueError("msg")
    resp = build_error_response(err, request_id=req_id)
    assert resp["request_id"] == req_id

def test_build_error_response_includes_timestamp():
    """Test build_error_response includes timestamp."""
    err = ValueError("msg")
    resp = build_error_response(err)
    assert "timestamp" in resp

def test_get_error_codes():
    """Test get_error_codes returns all error codes with required fields."""
    codes = get_error_codes()
    assert len(codes) > 0
    expected_codes = {
        "VALIDATION_ERROR", "CALCULATION_ERROR", "AUTHORIZATION_ERROR",
        "NOT_FOUND", "DUPLICATE", "CONCURRENT_MODIFICATION",
        "BUSINESS_RULE", "INTEGRATION_ERROR", "ERP_ERROR"
    }
    found_codes = {c["code"] for c in codes}
    assert found_codes == expected_codes

    for entry in codes:
        assert "code" in entry
        assert "http_status" in entry
        assert "description" in entry
        assert "example_message" in entry

def test_generate_request_id():
    """Test generate_request_id returns valid UUID4 format."""
    req_id = generate_request_id()
    # verify it's a valid UUID
    uuid_obj = uuid.UUID(req_id, version=4)
    assert str(uuid_obj) == req_id

"""
Custom error hierarchy for the ERP system.
All modules raise these exceptions for consistent error handling.
"""


from typing import Any

class ERPError(Exception):
    """Base exception for all ERP errors."""
    def __init__(self, message: str, code: str = "ERP_ERROR", details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ValidationError(ERPError):
    """Input validation failed."""
    def __init__(self, message: str, field: str = "", details: dict[str, Any] | None = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class NotFoundError(ERPError):
    """Requested resource not found."""
    def __init__(self, resource: str, resource_id: str = ""):
        msg = f"{resource} not found" + (f": {resource_id}" if resource_id else "")
        super().__init__(msg, "NOT_FOUND")


class DuplicateError(ERPError):
    """Resource already exists."""
    def __init__(self, resource: str, key: str = ""):
        msg = f"{resource} already exists" + (f": {key}" if key else "")
        super().__init__(msg, "DUPLICATE")


class BusinessRuleError(ERPError):
    """Business rule violation."""
    def __init__(self, message: str, rule: str = ""):
        super().__init__(message, "BUSINESS_RULE")
        self.rule = rule


class AuthorizationError(ERPError):
    """User lacks permission for this action."""
    def __init__(self, action: str = "", resource: str = ""):
        msg = f"Not authorized to {action}" + (f" on {resource}" if resource else "")
        super().__init__(msg, "AUTHORIZATION_ERROR")


class ConcurrentModificationError(ERPError):
    """Optimistic locking conflict."""
    def __init__(self, resource: str = ""):
        super().__init__(
            f"Concurrent modification detected{f' on {resource}' if resource else ''}",
            "CONCURRENT_MODIFICATION"
        )


class IntegrationError(ERPError):
    """External system integration failure."""
    def __init__(self, system: str, message: str):
        super().__init__(f"[{system}] {message}", "INTEGRATION_ERROR")


class CalculationError(ERPError):
    """Calculation error (tax, depreciation, etc)."""
    def __init__(self, message: str):
        super().__init__(message, "CALCULATION_ERROR")

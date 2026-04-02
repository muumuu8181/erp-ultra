from shared.errors import ValidationError


VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}

def validate_http_method(method: str) -> None:
    """
    Validates that the provided HTTP method is a recognized, valid method.

    Args:
        method: The HTTP method string to validate.

    Raises:
        ValidationError: If the method is not in the recognized list.
    """
    if method.upper() not in VALID_HTTP_METHODS:
        raise ValidationError(f"Invalid HTTP method: {method}. Must be one of {VALID_HTTP_METHODS}")

def validate_endpoint_path(path: str) -> None:
    """
    Validates that the provided path starts with a slash.

    Args:
        path: The path string to validate.

    Raises:
        ValidationError: If the path does not start with a slash.
    """
    if not path.startswith("/"):
        raise ValidationError("Endpoint path must start with a slash ('/')")

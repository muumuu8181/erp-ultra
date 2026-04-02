def validate_attachment_name(name: str) -> bool:
    """Validate that the attachment name is not empty."""
    return bool(name and name.strip())

def validate_attachment_code(code: str) -> bool:
    """Validate that the attachment code is not empty."""
    return bool(code and code.strip())

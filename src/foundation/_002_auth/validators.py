import re
from shared.errors import ValidationError

def validate_password_strength(password: str) -> None:
    """
    Validate password meets strength requirements.
    Rules: minimum 8 characters, at least 1 uppercase letter, at least 1 digit.
    Raises ValidationError with field="password" if any rule is violated.
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long", field="password")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least 1 uppercase letter", field="password")

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least 1 digit", field="password")

def validate_email_format(email: str) -> None:
    """
    Validate email has correct format using regex pattern.
    Raises ValidationError with field="email" if format is invalid.
    Use pattern: r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'
    """
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format", field="email")

def validate_username_format(username: str) -> None:
    """
    Validate username format.
    Rules: 3-50 characters, alphanumeric + underscores only.
    Raises ValidationError with field="username" if format is invalid.
    """
    if len(username) < 3 or len(username) > 50:
        raise ValidationError("Username must be between 3 and 50 characters", field="username")

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError("Username can only contain alphanumeric characters and underscores", field="username")

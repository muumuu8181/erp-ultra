from shared.errors import ValidationError
from .schemas import LogEntryCreate

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"}

def validate_log_level(level: str) -> None:
    """Validate that the log level is one of the standard levels."""
    if level.upper() not in VALID_LOG_LEVELS:
        raise ValidationError(
            f"Invalid log level: {level}. Must be one of {', '.join(VALID_LOG_LEVELS)}",
            field="level"
        )

def validate_log_entry_create(data: LogEntryCreate) -> None:
    """Validate a LogEntryCreate object before saving."""
    validate_log_level(data.level)

    if not data.message.strip():
        raise ValidationError("Log message cannot be empty", field="message")

    if not data.module.strip():
        raise ValidationError("Log module cannot be empty", field="module")

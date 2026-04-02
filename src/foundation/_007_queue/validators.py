import json
import re

from shared.errors import ValidationError

QUEUE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,99}$")

def validate_queue_name(queue_name: str) -> None:
    """
    Validate queue name format.
    Rules: 2-100 characters, lowercase alphanumeric + underscores + hyphens.
    Raises ValidationError with field="queue_name" if invalid.
    """
    if not QUEUE_NAME_PATTERN.match(queue_name):
        raise ValidationError("Invalid queue name format.", field="queue_name")

def validate_json_payload(payload: str) -> None:
    """
    Validate payload is valid JSON.
    - Parse with json.loads()
    - Raise ValidationError with field="payload" if not valid JSON
    """
    try:
        json.loads(payload)
    except json.JSONDecodeError:
        raise ValidationError("Invalid JSON payload.", field="payload")

def validate_max_retries(max_retries: int) -> None:
    """
    Validate max_retries is reasonable.
    Rules: must be >= 0 and <= 10.
    Raises ValidationError with field="max_retries" if invalid.
    """
    if not (0 <= max_retries <= 10):
        raise ValidationError("max_retries must be between 0 and 10.", field="max_retries")

def validate_priority(priority: int) -> None:
    """
    Validate priority value.
    Rules: must be >= 0 and <= 100.
    Raises ValidationError with field="priority" if invalid.
    """
    if not (0 <= priority <= 100):
        raise ValidationError("priority must be between 0 and 100.", field="priority")

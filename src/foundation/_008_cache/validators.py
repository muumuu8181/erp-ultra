import json
import re
from shared.errors import ValidationError

# Pre-compile regex for performance
CACHE_KEY_REGEX = re.compile(r'^[a-z][a-z0-9_]*(:[a-z0-9_]+)+$')

KNOWN_MODULES = {
    "system", "auth", "rbac", "gateway", "config",
    "logging", "queue", "cache", "inventory", "orders",
    "customers", "accounting", "reports", "hr"
}

def validate_cache_key(key: str) -> None:
    """
    Validate cache key format: module:entity:id
    Rules:
    - Must match pattern: colon-separated segments
    - Pattern: r'^[a-z][a-z0-9_]*(:[a-z][a-z0-9_]*)+$'
    - Minimum 2 segments (e.g., "inventory:products" is valid)
    - Maximum 5 segments
    - Total length <= 50
    Raises ValidationError with field="key" if invalid.
    """
    if len(key) > 50:
        raise ValidationError("Key length exceeds 50 characters", field="key")
    if not CACHE_KEY_REGEX.match(key):
        raise ValidationError("Key does not match required pattern", field="key")
    segments = key.split(':')
    if len(segments) > 5:
        raise ValidationError("Key has too many segments (max 5)", field="key")

def validate_cache_value(value: str) -> None:
    """
    Validate cache value is valid JSON.
    - Parse with json.loads()
    - Raise ValidationError with field="value" if not valid JSON
    """
    try:
        json.loads(value)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON value: {e}", field="value")

def validate_ttl(ttl_seconds: int) -> None:
    """
    Validate TTL is reasonable.
    Rules: must be >= 1 and <= 86400 (1 day).
    Raises ValidationError with field="ttl_seconds" if invalid.
    """
    if not (1 <= ttl_seconds <= 86400):
        raise ValidationError("TTL must be between 1 and 86400 seconds", field="ttl_seconds")

def validate_module_name(module: str) -> None:
    """
    Validate module name.
    Known modules: ["system", "auth", "rbac", "gateway", "config",
                    "logging", "queue", "cache", "inventory", "orders",
                    "customers", "accounting", "reports", "hr"]
    Raises ValidationError with field="module" if not in known list.
    """
    if module not in KNOWN_MODULES:
        raise ValidationError(f"Unknown module name: {module}", field="module")

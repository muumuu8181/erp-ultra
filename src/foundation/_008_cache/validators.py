import json
import re
from shared.errors import ValidationError

# Known modules list
KNOWN_MODULES = [
    "system", "auth", "rbac", "gateway", "config",
    "logging", "queue", "cache", "inventory", "orders",
    "customers", "accounting", "reports", "hr"
]

CACHE_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*(:[a-z][a-z0-9_]*)*(:[a-z0-9_]+)$')


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
        raise ValidationError("Cache key length must be <= 50", field="key")

    segments = key.split(":")
    if len(segments) < 2:
        raise ValidationError("Cache key must have at least 2 segments", field="key")
    if len(segments) > 5:
        raise ValidationError("Cache key must have at most 5 segments", field="key")

    if not re.match(r'^[a-z][a-z0-9_]*(:[a-z][a-z0-9_]*)*(:[0-9a-z_]+)$', key):
        raise ValidationError("Cache key does not match required pattern", field="key")


def validate_cache_value(value: str) -> None:
    """
    Validate cache value is valid JSON.
    - Parse with json.loads()
    - Raise ValidationError with field="value" if not valid JSON
    """
    try:
        json.loads(value)
    except (ValueError, TypeError):
        raise ValidationError("Cache value must be valid JSON", field="value")


def validate_ttl(ttl_seconds: int) -> None:
    """
    Validate TTL is reasonable.
    Rules: must be >= 1 and <= 86400 (1 day).
    Raises ValidationError with field="ttl_seconds" if invalid.
    """
    if not isinstance(ttl_seconds, int) or ttl_seconds < 1 or ttl_seconds > 86400:
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

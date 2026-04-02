from shared.errors import ValidationError


def validate_effect(effect: str) -> None:
    """Validates that effect is either 'allow' or 'deny'."""
    if effect not in ("allow", "deny"):
        raise ValidationError(f"Invalid effect '{effect}'. Must be 'allow' or 'deny'.")

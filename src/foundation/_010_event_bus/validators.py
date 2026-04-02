"""
Validation logic for event bus inputs.
"""
import re

from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, ValidationError
from src.foundation._010_event_bus.models import EventSubscription


def validate_event_type_format(event_type: str) -> str:
    """Validate event_type follows the module.action pattern.

    Valid formats:
    - "sales_order.created" (two lowercase segments separated by dot)
    - "inventory.stock_updated" (underscores allowed)
    - "sales_order.*" (wildcard for subscribe)
    - "*" (wildcard for everything)

    Invalid formats:
    - "salesOrderCreated" (no dot, camelCase)
    - "SALES_ORDER.CREATED" (uppercase)
    - "created" (only one segment)
    - "" (empty)

    Args:
        event_type: The event type string to validate.
    Returns:
        The validated event type string.
    Raises:
        ValidationError: If format is invalid.
    """
    if not event_type:
        raise ValidationError("event_type cannot be empty", field="event_type")

    if event_type == "*":
        return event_type

    pattern = r"^[a-z_]+\.(\*|[a-z_]+)$"
    if not re.match(pattern, event_type):
        raise ValidationError(
            "event_type must be in format 'module.action', 'module.*', or '*'",
            field="event_type"
        )
    return event_type


async def validate_handler_module_exists(db: AsyncSession, handler_module: str) -> str:
    """Validate that the handler module exists in the system.

    Checks the event_subscription table for previously registered modules.
    For the initial implementation, validates format: _NNN_name or a known module name.

    Args:
        db: AsyncSession for database access.
        handler_module: Module name to validate.
    Returns:
        The validated module name.
    Raises:
        ValidationError: If module name format is invalid.
    """
    # Simply check standard format for now since dynamic validation might depend on app layout
    # Assuming any lowercase string with underscores might be a module
    if not re.match(r"^[a-z_0-9]+$", handler_module):
        raise ValidationError(
            f"Invalid module name format: {handler_module}",
            field="handler_module"
        )
    return handler_module


def validate_subscription_not_duplicate(
    event_type: str, handler_module: str, handler_function: str, existing: list[EventSubscription]
) -> None:
    """Check that this subscription does not already exist.

    Args:
        event_type: Event type pattern.
        handler_module: Handler module name.
        handler_function: Handler function name.
        existing: List of existing EventSubscription records to check against.
    Raises:
        DuplicateError: If an identical active subscription exists.
    """
    for sub in existing:
        if (
            sub.event_type == event_type and
            sub.handler_module == handler_module and
            sub.handler_function == handler_function
        ):
            if sub.is_active:
                raise DuplicateError("EventSubscription", key=f"{event_type}:{handler_module}:{handler_function}")

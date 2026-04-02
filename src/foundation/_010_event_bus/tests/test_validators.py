import pytest
from shared.errors import ValidationError, DuplicateError
from src.foundation._010_event_bus.validators import (
    validate_event_type_format, validate_handler_module_exists, validate_subscription_not_duplicate
)
from src.foundation._010_event_bus.models import EventSubscription

def test_validate_event_type_format():
    assert validate_event_type_format("module.action") == "module.action"
    assert validate_event_type_format("sales_order.created") == "sales_order.created"
    assert validate_event_type_format("sales_order.*") == "sales_order.*"
    assert validate_event_type_format("*") == "*"

    with pytest.raises(ValidationError):
        validate_event_type_format("no_dot")
    with pytest.raises(ValidationError):
        validate_event_type_format("UPPER.CASE")
    with pytest.raises(ValidationError):
        validate_event_type_format("")

@pytest.mark.asyncio
async def test_validate_handler_module_exists(db_session):
    assert await validate_handler_module_exists(db_session, "valid_module") == "valid_module"

    with pytest.raises(ValidationError):
        await validate_handler_module_exists(db_session, "INVALID-MODULE")

def test_validate_subscription_not_duplicate():
    existing = [
        EventSubscription(event_type="test.*", handler_module="test", handler_function="func", is_active=True)
    ]

    # Should pass
    validate_subscription_not_duplicate("test.other", "test", "func", existing)
    validate_subscription_not_duplicate("test.*", "other", "func", existing)

    # Should fail
    with pytest.raises(DuplicateError):
        validate_subscription_not_duplicate("test.*", "test", "func", existing)

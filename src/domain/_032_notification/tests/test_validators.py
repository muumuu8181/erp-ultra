import pytest
from src.domain._032_notification.schemas import NotificationCreate, NotificationTemplateCreate
from src.domain._032_notification.validators import validate_notification_create, validate_template_code_unique
from src.domain._032_notification.models import ChannelEnum, StatusEnum, PriorityEnum
from shared.errors import ValidationError

@pytest.mark.asyncio
async def test_user_id_required_validation():
    data = NotificationCreate(
        user_id="  ",
        channel=ChannelEnum.in_app,
        subject="S",
        body="B"
    )
    with pytest.raises(ValidationError) as exc:
        await validate_notification_create(data)
    assert exc.value.field == "user_id"

@pytest.mark.asyncio
async def test_template_variable_completeness():
    data = NotificationCreate(
        user_id="U1",
        channel=ChannelEnum.email,
        subject="S",
        body="B",
        template_vars={"x": "val1"}
    )

    # Template requires y which is missing
    with pytest.raises(ValidationError) as exc:
        await validate_notification_create(data, template_body="Hello {{x}} {{y}}")
    assert "Missing template variable: y" in str(exc.value)

@pytest.mark.asyncio
async def test_template_variable_missing_dict():
    data = NotificationCreate(
        user_id="U1",
        channel=ChannelEnum.email,
        subject="S",
        body="B",
        template_vars=None
    )

    # Template expects variables but none provided
    with pytest.raises(ValidationError) as exc:
        await validate_notification_create(data, template_body="Hello {{x}}")
    assert "Template variables are required" in str(exc.value)

def test_valid_channel_pass_fail():
    # Pydantic enum validation
    with pytest.raises(ValueError):
        NotificationCreate(
            user_id="U1",
            channel="invalid_channel",
            subject="S",
            body="B"
        )

def test_valid_status_priority_enum_checks():
    # Pydantic enum validation
    with pytest.raises(ValueError):
        NotificationCreate(
            user_id="U1",
            channel=ChannelEnum.email,
            subject="S",
            body="B",
            priority="invalid_priority"
        )

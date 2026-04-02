import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.domain._032_notification.models import NotificationTemplate, Notification, ChannelEnum, StatusEnum, PriorityEnum
from datetime import datetime

@pytest.mark.asyncio
async def test_notification_template_creation(async_session):
    template = NotificationTemplate(
        code="TPL_01",
        name="Test Template",
        subject="Hello {{name}}",
        body_template="Hi {{name}}, your code is {{code}}",
        channel=ChannelEnum.email,
        module="test"
    )
    async_session.add(template)
    await async_session.commit()

    result = await async_session.execute(select(NotificationTemplate).where(NotificationTemplate.code == "TPL_01"))
    db_template = result.scalars().first()

    assert db_template is not None
    assert db_template.name == "Test Template"
    assert db_template.channel == ChannelEnum.email
    assert db_template.is_active is True

@pytest.mark.asyncio
async def test_notification_template_unique_code(async_session):
    template1 = NotificationTemplate(
        code="TPL_UNIQ",
        name="Test 1",
        subject="S1",
        body_template="B1",
        channel=ChannelEnum.in_app,
        module="test"
    )
    async_session.add(template1)
    await async_session.commit()

    template2 = NotificationTemplate(
        code="TPL_UNIQ",  # Duplicate code
        name="Test 2",
        subject="S2",
        body_template="B2",
        channel=ChannelEnum.email,
        module="test"
    )
    async_session.add(template2)
    with pytest.raises(IntegrityError):
        await async_session.commit()

@pytest.mark.asyncio
async def test_notification_creation_and_fk(async_session):
    template = NotificationTemplate(
        code="TPL_02",
        name="FK Template",
        subject="S",
        body_template="B",
        channel=ChannelEnum.slack,
        module="test"
    )
    async_session.add(template)
    await async_session.commit()

    notification = Notification(
        template_id=template.id,
        user_id="U1",
        channel=ChannelEnum.slack,
        subject="S",
        body="B",
        priority=PriorityEnum.high
    )
    async_session.add(notification)
    await async_session.commit()

    result = await async_session.execute(select(Notification).where(Notification.user_id == "U1"))
    db_notif = result.scalars().first()

    assert db_notif is not None
    assert db_notif.template_id == template.id
    assert db_notif.status == StatusEnum.pending
    assert db_notif.priority == PriorityEnum.high

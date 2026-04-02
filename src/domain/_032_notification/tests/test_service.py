import pytest
from sqlalchemy import select
from datetime import datetime

from src.domain._032_notification import service
from src.domain._032_notification.schemas import (
    NotificationCreate,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationFilter
)
from src.domain._032_notification.models import ChannelEnum, StatusEnum, PriorityEnum, Notification
from shared.errors import ValidationError, DuplicateError, NotFoundError

@pytest.mark.asyncio
async def test_send_notification_without_template(async_session):
    data = NotificationCreate(
        user_id="U1",
        channel=ChannelEnum.in_app,
        subject="No Template",
        body="Plain body",
        priority=PriorityEnum.high
    )

    notif = await service.send_notification(async_session, data)

    assert notif.id is not None
    assert notif.user_id == "U1"
    assert notif.channel == ChannelEnum.in_app
    assert notif.status == StatusEnum.sent  # In-app becomes sent
    assert notif.sent_at is not None

@pytest.mark.asyncio
async def test_create_template_success(async_session):
    data = NotificationTemplateCreate(
        code="TPL_SERV_1",
        name="Serv Template",
        subject="Subject {{x}}",
        body_template="Body {{x}} {{y}}",
        channel=ChannelEnum.email,
        module="mod"
    )

    tpl = await service.create_template(async_session, data)
    assert tpl.id is not None
    assert tpl.code == "TPL_SERV_1"

@pytest.mark.asyncio
async def test_create_template_duplicate(async_session):
    data = NotificationTemplateCreate(
        code="TPL_DUP",
        name="Serv Template",
        subject="Subject",
        body_template="Body",
        channel=ChannelEnum.email,
        module="mod"
    )
    await service.create_template(async_session, data)

    with pytest.raises(DuplicateError):
        await service.create_template(async_session, data)

@pytest.mark.asyncio
async def test_get_update_delete_template(async_session):
    data = NotificationTemplateCreate(
        code="TPL_CRUD",
        name="Serv Template",
        subject="Subject",
        body_template="Body",
        channel=ChannelEnum.email,
        module="mod"
    )
    tpl = await service.create_template(async_session, data)

    fetched = await service.get_template(async_session, tpl.id)
    assert fetched.id == tpl.id

    update_data = NotificationTemplateUpdate(name="Updated")
    updated = await service.update_template(async_session, tpl.id, update_data)
    assert updated.name == "Updated"

    await service.delete_template(async_session, tpl.id)

    with pytest.raises(NotFoundError):
        await service.get_template(async_session, tpl.id)

@pytest.mark.asyncio
async def test_send_notification_with_template(async_session):
    tpl_data = NotificationTemplateCreate(
        code="TPL_VAR",
        name="Var Template",
        subject="Sub {{a}}",
        body_template="Bod {{b}}",
        channel=ChannelEnum.slack,
        module="mod"
    )
    tpl = await service.create_template(async_session, tpl_data)

    data = NotificationCreate(
        template_id=tpl.id,
        user_id="U2",
        channel=ChannelEnum.slack,
        subject="",  # Overwritten
        body="",     # Overwritten
        template_vars={"a": "Hello", "b": "World"}
    )

    notif = await service.send_notification(async_session, data)
    assert notif.subject == "Sub Hello"
    assert notif.body == "Bod World"
    assert notif.status == StatusEnum.pending

@pytest.mark.asyncio
async def test_send_bulk(async_session):
    data = NotificationCreate(
        user_id="bulk_placeholder", # Replaced by send_bulk
        channel=ChannelEnum.email,
        subject="Bulk",
        body="Message"
    )

    notifs = await service.send_bulk(async_session, ["U3", "U4"], data)
    assert len(notifs) == 2

    # Needs to be awaited/refreshed properly, or just accessing directly works if loaded.
    # We must ensure we do not touch expired attributes outside greenlet
    # Actually, in tests, because we don't have session.refresh inside test,
    # we can just select them to check or access them if they are still attached and loaded
    # They should be loaded because send_notification does db.refresh(notification)
    assert notifs[0].user_id == "U3"
    assert notifs[1].user_id == "U4"

@pytest.mark.asyncio
async def test_mark_as_read(async_session):
    data = NotificationCreate(
        user_id="U5",
        channel=ChannelEnum.in_app,
        subject="Sub",
        body="Bod"
    )
    notif = await service.send_notification(async_session, data)

    assert notif.status == StatusEnum.sent
    assert notif.read_at is None

    updated = await service.mark_as_read(async_session, notif.id)
    assert updated.status == StatusEnum.read
    assert updated.read_at is not None

@pytest.mark.asyncio
async def test_get_unread_count(async_session):
    for i in range(3):
        data = NotificationCreate(
            user_id="U6",
            channel=ChannelEnum.in_app,
            subject=f"Sub {i}",
            body="Bod"
        )
        await service.send_notification(async_session, data)

    count = await service.get_unread_count(async_session, "U6")
    assert count == 3

@pytest.mark.asyncio
async def test_get_notifications_with_filters_and_pagination(async_session):
    for i in range(5):
        data = NotificationCreate(
            user_id="U7",
            channel=ChannelEnum.email,
            subject=f"Sub {i}",
            body="Bod"
        )
        await service.send_notification(async_session, data)

    # Test Pagination
    filters = NotificationFilter(user_id="U7", page=1, size=2)
    res = await service.get_notifications(async_session, filters)
    assert res.total == 5
    assert len(res.items) == 2
    assert res.total_pages == 3

@pytest.mark.asyncio
async def test_get_stats(async_session):
    data = NotificationCreate(
        user_id="U8",
        channel=ChannelEnum.in_app,
        subject="S",
        body="B"
    )
    await service.send_notification(async_session, data)

    data2 = NotificationCreate(
        user_id="U8",
        channel=ChannelEnum.email,
        subject="S2",
        body="B2"
    )
    await service.send_notification(async_session, data2)

    stats = await service.get_stats(async_session, "U8")
    assert stats.total == 2
    assert stats.by_channel[ChannelEnum.in_app] == 1
    assert stats.by_channel[ChannelEnum.email] == 1
    assert stats.by_status[StatusEnum.sent] == 1
    assert stats.by_status[StatusEnum.pending] == 1
    assert stats.unread_count == 1

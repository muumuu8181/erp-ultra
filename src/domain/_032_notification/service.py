import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from shared.types import PaginatedResponse
from shared.errors import NotFoundError
from src.domain._032_notification.models import Notification, NotificationTemplate, ChannelEnum, StatusEnum
from src.domain._032_notification.schemas import NotificationCreate, NotificationTemplateCreate, NotificationTemplateUpdate, NotificationFilter, NotificationStats, NotificationResponse
from src.domain._032_notification.validators import validate_notification_create, validate_template_code_unique

async def render_template(db: AsyncSession, template_id: int, variables: dict[str, str]) -> tuple[str, str]:
    """Render a template with variable substitution. Returns (subject, body).
    Template syntax: {{variable_name}}. Replace with values from variables dict.
    """
    template = await db.get(NotificationTemplate, template_id)
    if not template:
        raise NotFoundError("NotificationTemplate", str(template_id))

    subject = template.subject
    body = template.body_template

    for key, value in variables.items():
        subject = re.sub(r"\{\{\s*" + re.escape(key) + r"\s*\}\}", lambda m, v=value: str(v), subject)
        body = re.sub(r"\{\{\s*" + re.escape(key) + r"\s*\}\}", lambda m, v=value: str(v), body)

    return subject, body

async def send_notification(db: AsyncSession, data: NotificationCreate) -> Notification:
    """Send a notification. If template_id is provided, render template with template_vars.
    For in_app: store in DB with status sent.
    For email/slack: store in DB with status pending and log (placeholder).
    """
    template_body = None
    if data.template_id:
        template = await db.get(NotificationTemplate, data.template_id)
        if not template:
            raise NotFoundError("NotificationTemplate", str(data.template_id))
        template_body = template.body_template

    await validate_notification_create(data, template_body)

    subject = data.subject
    body = data.body

    if data.template_id and data.template_vars:
        subject, body = await render_template(db, data.template_id, data.template_vars)

    status = StatusEnum.sent if data.channel == ChannelEnum.in_app else StatusEnum.pending
    sent_at = datetime.now() if data.channel == ChannelEnum.in_app else None

    # Placeholder for actual email/slack dispatch
    if data.channel in (ChannelEnum.email, ChannelEnum.slack):
        print(f"[{data.channel.value.upper()}] To: {data.user_id} | Subject: {subject} | Body: {body}")

    notification = Notification(
        template_id=data.template_id,
        user_id=data.user_id,
        channel=data.channel,
        subject=subject,
        body=body,
        priority=data.priority,
        status=status,
        scheduled_at=data.scheduled_at,
        sent_at=sent_at,
        reference_type=data.reference_type,
        reference_id=data.reference_id,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification

async def send_bulk(db: AsyncSession, user_ids: list[str], data: NotificationCreate) -> list[Notification]:
    """Send the same notification to multiple users."""
    notifications = []
    for uid in user_ids:
        # Create a copy for each user
        user_data = NotificationCreate(
            **{**data.model_dump(), "user_id": uid}
        )
        notif = await send_notification(db, user_data)
        notifications.append(notif)
    return notifications

async def mark_as_read(db: AsyncSession, notification_id: int) -> Notification:
    """Mark a single notification as read. Set status=read and read_at=now."""
    notification = await db.get(Notification, notification_id)
    if not notification:
        raise NotFoundError("Notification", str(notification_id))

    notification.status = StatusEnum.read
    notification.read_at = datetime.now()
    await db.commit()
    await db.refresh(notification)
    return notification

async def get_unread_count(db: AsyncSession, user_id: str) -> int:
    """Return count of unread notifications for a user."""
    stmt = select(func.count()).where(
        Notification.user_id == user_id,
        Notification.status == StatusEnum.sent
    )
    result = await db.execute(stmt)
    return result.scalar_one()

async def get_notifications(db: AsyncSession, filters: NotificationFilter) -> PaginatedResponse[NotificationResponse]:
    """List notifications with filtering and pagination."""
    query = select(Notification)

    if filters.user_id:
        query = query.where(Notification.user_id == filters.user_id)
    if filters.channel:
        query = query.where(Notification.channel == filters.channel)
    if filters.status:
        query = query.where(Notification.status == filters.status)
    if filters.priority:
        query = query.where(Notification.priority == filters.priority)
    if filters.reference_type:
        query = query.where(Notification.reference_type == filters.reference_type)
    if filters.reference_id:
        query = query.where(Notification.reference_id == filters.reference_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (filters.page - 1) * filters.size
    query = query.offset(offset).limit(filters.size)

    result = await db.execute(query)
    items = list(result.scalars().all())
    response_items = [NotificationResponse.model_validate(item) for item in items]

    total_pages = (total + filters.size - 1) // filters.size if filters.size > 0 else 0

    return PaginatedResponse(
        items=response_items,
        total=total,
        page=filters.page,
        page_size=filters.size,
        total_pages=total_pages
    )

async def create_template(db: AsyncSession, data: NotificationTemplateCreate) -> NotificationTemplate:
    """Create a new notification template."""
    await validate_template_code_unique(db, data.code)

    template = NotificationTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template

async def get_template(db: AsyncSession, template_id: int) -> NotificationTemplate:
    """Get a notification template by ID."""
    template = await db.get(NotificationTemplate, template_id)
    if not template:
        raise NotFoundError("NotificationTemplate", str(template_id))
    return template

async def update_template(db: AsyncSession, template_id: int, data: NotificationTemplateUpdate) -> NotificationTemplate:
    """Update a notification template."""
    template = await get_template(db, template_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)

    await db.commit()
    await db.refresh(template)
    return template

async def delete_template(db: AsyncSession, template_id: int) -> None:
    """Delete a notification template."""
    template = await get_template(db, template_id)
    await db.delete(template)
    await db.commit()

async def get_stats(db: AsyncSession, user_id: str | None = None) -> NotificationStats:
    """Return notification statistics, optionally filtered by user."""
    query = select(Notification)
    if user_id:
        query = query.where(Notification.user_id == user_id)

    result = await db.execute(query)
    notifications = result.scalars().all()

    total = len(notifications)
    by_status: dict[str, int] = {}
    by_channel: dict[str, int] = {}
    unread_count = 0

    for n in notifications:
        by_status[n.status.value] = by_status.get(n.status.value, 0) + 1
        by_channel[n.channel.value] = by_channel.get(n.channel.value, 0) + 1
        if n.status == StatusEnum.sent:
            unread_count += 1

    return NotificationStats(
        total=total,
        by_status=by_status,
        by_channel=by_channel,
        unread_count=unread_count
    )

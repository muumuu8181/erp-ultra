import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.errors import ValidationError, DuplicateError
from src.domain._032_notification.models import NotificationTemplate

async def validate_notification_create(data, template_body: str | None = None) -> None:
    if not data.user_id or not data.user_id.strip():
        raise ValidationError("user_id must be a non-empty string", field="user_id")

    if template_body:
        placeholders = re.findall(r"\{\{([^}]+)\}\}", template_body)
        if placeholders:
            if not data.template_vars:
                raise ValidationError("Template variables are required", field="template_vars")
            for ph in placeholders:
                ph = ph.strip()
                if ph not in data.template_vars:
                    raise ValidationError(f"Missing template variable: {ph}", field="template_vars")

async def validate_template_code_unique(db: AsyncSession, code: str) -> None:
    stmt = select(NotificationTemplate).where(NotificationTemplate.code == code)
    result = await db.execute(stmt)
    if result.scalars().first() is not None:
        raise DuplicateError("NotificationTemplate", key=code)

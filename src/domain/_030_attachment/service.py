from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import Attachment
from .schemas import AttachmentCreate, AttachmentResponse


async def create_attachment(db: AsyncSession, attachment_in: AttachmentCreate) -> AttachmentResponse:
    """Create a new attachment."""
    attachment = Attachment(**attachment_in.model_dump())
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return AttachmentResponse.model_validate(attachment)


async def get_attachment(db: AsyncSession, attachment_id: int) -> AttachmentResponse | None:
    """Get an attachment by ID."""
    result = await db.execute(select(Attachment).where(Attachment.id == attachment_id))
    attachment = result.scalar_one_or_none()
    if attachment:
        return AttachmentResponse.model_validate(attachment)
    return None

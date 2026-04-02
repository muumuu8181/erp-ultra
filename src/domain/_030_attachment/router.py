from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import AttachmentCreate, AttachmentResponse
from .service import create_attachment, get_attachment

from src.foundation._001_database import get_db

router = APIRouter(prefix="/api/v1/attachment", tags=["attachment"])


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def create_attachment_endpoint(
    attachment_in: AttachmentCreate,
    db: AsyncSession = Depends(get_db)
) -> AttachmentResponse:
    """Create a new attachment."""
    return await create_attachment(db, attachment_in)


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment_endpoint(
    attachment_id: int,
    db: AsyncSession = Depends(get_db)
) -> AttachmentResponse:
    """Get an attachment by ID."""
    attachment = await get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment

"""
Module 030: Attachment

Provides domain models and APIs for handling attachments.
"""

from .models import Attachment
from .schemas import AttachmentCreate, AttachmentResponse, AttachmentUpdate
from .service import create_attachment, get_attachment
from .router import router

__all__ = [
    "Attachment",
    "AttachmentCreate",
    "AttachmentResponse",
    "AttachmentUpdate",
    "create_attachment",
    "get_attachment",
    "router",
]

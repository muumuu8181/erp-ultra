"""
_025_document_number - Document Number Generator.

Provides:
- DocumentSequence model for managing sequences.
- DocumentSequenceService for safe concurrent number generation.
- FastAPI router for CRUD and generation.
"""

from src.domain._025_document_number.models import DocumentSequence
from src.domain._025_document_number.router import router
from src.domain._025_document_number.schemas import (
    DocumentSequenceCreate,
    DocumentSequenceResponse,
    DocumentSequenceUpdate,
    GeneratedDocumentNumberResponse,
)
from src.domain._025_document_number.service import DocumentSequenceService

__all__ = [
    "DocumentSequence",
    "DocumentSequenceCreate",
    "DocumentSequenceUpdate",
    "DocumentSequenceResponse",
    "GeneratedDocumentNumberResponse",
    "DocumentSequenceService",
    "router",
]

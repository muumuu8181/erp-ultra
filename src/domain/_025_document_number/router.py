"""
FastAPI router for Document Number Generator.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import BusinessRuleError, DuplicateError, NotFoundError, ValidationError
from shared.types import PaginatedResponse
from src.domain._025_document_number.schemas import (
    DocumentSequenceCreate,
    DocumentSequenceResponse,
    DocumentSequenceUpdate,
    GeneratedDocumentNumberResponse,
)
from src.domain._025_document_number.service import DocumentSequenceService
from src.foundation._001_database import get_db

router = APIRouter(prefix="/api/v1/document-numbers", tags=["document-numbers"])
service = DocumentSequenceService()


@router.post("", response_model=DocumentSequenceResponse, status_code=status.HTTP_201_CREATED)
async def create_sequence(
    data: DocumentSequenceCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new document sequence."""
    try:
        user = "system" # Hardcoded user for now, replace with actual user when auth is implemented
        return await service.create(db, data, user)
    except (DuplicateError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=PaginatedResponse[DocumentSequenceResponse])
async def list_sequences(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List document sequences."""
    items, total = await service.list(db, skip=skip, limit=limit)
    total_pages = (total + limit - 1) // limit
    page = (skip // limit) + 1

    # We construct a dict to match PaginatedResponse schema
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit,
        "total_pages": total_pages
    }


@router.get("/{id}", response_model=DocumentSequenceResponse)
async def get_sequence(
    id: int,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get a document sequence by ID."""
    try:
        return await service.get(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{id}", response_model=DocumentSequenceResponse)
async def update_sequence(
    id: int,
    data: DocumentSequenceUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update a document sequence."""
    try:
        user = "system" # Hardcoded user for now
        return await service.update(db, id, data, user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sequence(
    id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a document sequence."""
    try:
        await service.delete(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/generate/{prefix}", response_model=GeneratedDocumentNumberResponse)
async def generate_number(
    prefix: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Generate the next document number for the given prefix."""
    try:
        return await service.generate_next_number(db, prefix)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

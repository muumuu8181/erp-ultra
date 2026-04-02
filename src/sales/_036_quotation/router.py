"""
Router for the _036_quotation module.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.types import PaginatedResponse, DocumentStatus
from src.foundation._001_database.engine import get_db
from src.sales._036_quotation.schemas import (
    QuotationCreate,
    QuotationUpdate,
    QuotationResponse,
    QuotationListFilter
)
from src.sales._036_quotation import service

router = APIRouter(prefix="/api/v1/quotations", tags=["Quotation"])


@router.post("/", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
async def create_quotation_endpoint(data: QuotationCreate, db: AsyncSession = Depends(get_db)):
    """Create a new quotation."""
    return await service.create_quotation(db, data)


@router.get("/", response_model=PaginatedResponse[QuotationResponse])
async def list_quotations_endpoint(
    filter_params: QuotationListFilter = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """List quotations with optional filtering and pagination."""
    return await service.list_quotations(db, filter_params)


@router.get("/expired", response_model=PaginatedResponse[QuotationResponse])
async def list_expired_quotations_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List quotations that have expired (valid_until is in the past)."""
    filters = QuotationListFilter(is_expired=True, page=page, page_size=page_size)
    return await service.list_quotations(db, filters)


@router.get("/{quotation_id}", response_model=QuotationResponse)
async def get_quotation_endpoint(quotation_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific quotation by ID."""
    return await service.get_quotation(db, quotation_id)


@router.put("/{quotation_id}", response_model=QuotationResponse)
async def update_quotation_endpoint(quotation_id: int, data: QuotationUpdate, db: AsyncSession = Depends(get_db)):
    """Update a draft quotation."""
    return await service.update_quotation(db, quotation_id, data)


@router.post("/{quotation_id}/send", response_model=QuotationResponse)
async def send_quotation_endpoint(quotation_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a quotation as sent."""
    return await service.send_quotation(db, quotation_id)


@router.post("/{quotation_id}/approve", response_model=QuotationResponse)
async def approve_quotation_endpoint(quotation_id: int, db: AsyncSession = Depends(get_db)):
    """Approve a quotation."""
    return await service.approve_quotation(db, quotation_id)


@router.post("/{quotation_id}/reject", response_model=QuotationResponse)
async def reject_quotation_endpoint(quotation_id: int, db: AsyncSession = Depends(get_db)):
    """Reject a quotation."""
    return await service.reject_quotation(db, quotation_id)


@router.post("/{quotation_id}/convert", response_model=Dict[str, Any])
async def convert_to_order_endpoint(quotation_id: int, db: AsyncSession = Depends(get_db)):
    """Convert an approved quotation to a format ready for a sales order."""
    return await service.convert_to_order(db, quotation_id)

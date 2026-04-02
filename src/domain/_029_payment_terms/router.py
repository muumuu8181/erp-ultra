"""
FastAPI router for Payment Terms module.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import math

from shared.types import PaginatedResponse
from shared.errors import ERPError, ValidationError, NotFoundError, DuplicateError
from src.foundation._001_database import get_db
from src.domain._029_payment_terms.schemas import PaymentTermCreate, PaymentTermUpdate, PaymentTermResponse
from src.domain._029_payment_terms import service


router = APIRouter(prefix="/api/v1/payment-terms", tags=["Payment Terms"])


@router.post("", response_model=PaymentTermResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_term(
    data: PaymentTermCreate,
    db: AsyncSession = Depends(get_db)
) -> PaymentTermResponse:
    """
    Create a new Payment Term.
    """
    try:
        term = await service.create_payment_term(db, data)
        return PaymentTermResponse.model_validate(term)
    except (ValidationError, DuplicateError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ERPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PaginatedResponse[PaymentTermResponse])
async def list_payment_terms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[PaymentTermResponse]:
    """
    List Payment Terms.
    """
    try:
        terms, total = await service.list_payment_terms(db, skip=skip, limit=limit, is_active=is_active)

        items = [PaymentTermResponse.model_validate(term) for term in terms]

        # Calculate total pages
        total_pages = math.ceil(total / limit) if limit > 0 else 0
        page = (skip // limit) + 1 if limit > 0 else 1

        return PaginatedResponse[PaymentTermResponse](
            items=items,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages
        )
    except ERPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{term_id}", response_model=PaymentTermResponse)
async def get_payment_term(
    term_id: int,
    db: AsyncSession = Depends(get_db)
) -> PaymentTermResponse:
    """
    Get a specific Payment Term by ID.
    """
    try:
        term = await service.get_payment_term(db, term_id)
        return PaymentTermResponse.model_validate(term)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ERPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{term_id}", response_model=PaymentTermResponse)
async def update_payment_term(
    term_id: int,
    data: PaymentTermUpdate,
    db: AsyncSession = Depends(get_db)
) -> PaymentTermResponse:
    """
    Update a Payment Term.
    """
    try:
        term = await service.update_payment_term(db, term_id, data)
        return PaymentTermResponse.model_validate(term)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValidationError, DuplicateError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ERPError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_term(
    term_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a Payment Term.
    """
    try:
        await service.delete_payment_term(db, term_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ERPError as e:
        raise HTTPException(status_code=500, detail=str(e))

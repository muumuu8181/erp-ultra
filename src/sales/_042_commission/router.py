"""
FastAPI router for Sales Commission module.
"""
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

import math
from foundation._001_database import get_db
from .schemas import CommissionCreate, CommissionUpdate, CommissionResponse
from shared.types import PaginatedResponse
from . import service

router = APIRouter(
    prefix="/api/v1/sales-commission",
    tags=["Sales Commission"]
)

@router.post("/", response_model=CommissionResponse, status_code=status.HTTP_201_CREATED)
async def create_commission(
    data: CommissionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new sales commission."""
    return await service.create_commission(db, data)

@router.get("/{commission_id}", response_model=CommissionResponse)
async def get_commission(
    commission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a sales commission by ID."""
    return await service.get_commission(db, commission_id)

@router.put("/{commission_id}", response_model=CommissionResponse)
async def update_commission(
    commission_id: int,
    data: CommissionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a sales commission."""
    return await service.update_commission(db, commission_id, data)

@router.delete("/{commission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_commission(
    commission_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a sales commission."""
    await service.delete_commission(db, commission_id)

@router.get("/", response_model=PaginatedResponse[CommissionResponse])
async def list_commissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    salesperson_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List sales commissions."""
    items, total = await service.list_commissions(
        db, skip=skip, limit=limit, salesperson_id=salesperson_id
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 1
    )

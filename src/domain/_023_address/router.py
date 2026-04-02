"""
FastAPI router for Address Book module.
"""
from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared.types import PaginatedResponse
from src.foundation._001_database import get_db

from .schemas import AddressCreate, AddressUpdate, AddressResponse
from .service import create_address, get_address, update_address, delete_address, list_addresses
from .models import Address


router = APIRouter(prefix="/api/v1/addresses", tags=["addresses"])


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address_endpoint(
    schema: AddressCreate,
    db: AsyncSession = Depends(get_db)
) -> Address:
    """Create a new address."""
    return await create_address(db, schema)


@router.get("", response_model=PaginatedResponse[AddressResponse])
async def list_addresses_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[AddressResponse]:
    """List addresses with pagination."""
    items = await list_addresses(db, skip=skip, limit=limit)

    # Get total count
    total_stmt = select(func.count()).select_from(Address)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return PaginatedResponse[AddressResponse](
        items=[AddressResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages
    )


@router.get("/{address_id}", response_model=AddressResponse)
async def get_address_endpoint(
    address_id: int,
    db: AsyncSession = Depends(get_db)
) -> Address:
    """Get an address by ID."""
    return await get_address(db, address_id)


@router.put("/{address_id}", response_model=AddressResponse)
async def update_address_endpoint(
    address_id: int,
    schema: AddressUpdate,
    db: AsyncSession = Depends(get_db)
) -> Address:
    """Update an address by ID."""
    return await update_address(db, address_id, schema)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address_endpoint(
    address_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an address by ID."""
    await delete_address(db, address_id)

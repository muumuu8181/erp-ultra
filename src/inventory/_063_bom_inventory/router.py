"""
FastAPI router for BOM inventory module.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.foundation._001_database import get_db
from src.inventory._063_bom_inventory import service
from src.inventory._063_bom_inventory.schemas import (
    BOMCreate,
    BOMResponse,
    BOMWithItemsResponse,
    BOMItemCreate,
    BOMItemResponse
)

router = APIRouter(prefix="/api/v1/bom_inventory/boms", tags=["BOM Inventory"])


@router.post("", response_model=BOMResponse, status_code=status.HTTP_201_CREATED)
async def create_bom(bom_in: BOMCreate, db: AsyncSession = Depends(get_db)):
    """Create a new Bill of Materials (BOM)."""
    return await service.create_bom(db, bom_in)


@router.get("/{bom_id}", response_model=BOMWithItemsResponse)
async def get_bom(bom_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a BOM and its components."""
    return await service.get_bom(db, bom_id)


@router.get("", response_model=List[BOMResponse])
async def list_boms(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """List BOMs."""
    return await service.list_boms(db, skip=skip, limit=limit)


@router.put("/{bom_id}", response_model=BOMResponse)
async def update_bom(bom_id: int, bom_in: BOMCreate, db: AsyncSession = Depends(get_db)):
    """Update an existing BOM."""
    return await service.update_bom(db, bom_id, bom_in)


@router.delete("/{bom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bom(bom_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a BOM."""
    await service.delete_bom(db, bom_id)


@router.post("/{bom_id}/items", response_model=BOMItemResponse, status_code=status.HTTP_201_CREATED)
async def add_bom_item(bom_id: int, item_in: BOMItemCreate, db: AsyncSession = Depends(get_db)):
    """Add a component to an existing BOM."""
    return await service.add_bom_item(db, bom_id, item_in)


@router.delete("/{bom_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bom_item(bom_id: int, item_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a component from a BOM."""
    await service.remove_bom_item(db, bom_id, item_id)

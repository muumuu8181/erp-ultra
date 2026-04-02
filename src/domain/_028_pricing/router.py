from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import get_db
from src.domain._028_pricing.schemas import (
    PriceListCreate, PriceListResponse, PriceListItemCreate, PriceListItemResponse,
    PriceLookupRequest, PriceLookupResponse, DuplicateRequest
)
from src.domain._028_pricing import service
from shared.types import PaginatedResponse
from sqlalchemy import select, func
from src.domain._028_pricing.models import PriceListItem

router = APIRouter(tags=["pricing"])

# Price list management routes
pricelist_router = APIRouter(prefix="/api/v1/price-lists", tags=["price-lists"])
# Pricing lookup routes
pricing_router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])

from fastapi import HTTPException
from shared.errors import DuplicateError, NotFoundError, ValidationError

@pricelist_router.post("", response_model=PriceListResponse, status_code=status.HTTP_201_CREATED)
async def create_price_list_route(data: PriceListCreate, db: AsyncSession = Depends(get_db)):
    """Create price list"""
    try:
        return await service.create_price_list(db, data)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

@pricelist_router.get("", response_model=PaginatedResponse[PriceListResponse])
async def list_price_lists_route(
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List price lists"""
    return await service.list_price_lists(db, is_active, page, page_size)

@pricelist_router.put("/{id}", response_model=PriceListResponse)
async def update_price_list_route(id: int, data: PriceListCreate, db: AsyncSession = Depends(get_db)):
    """Update price list"""
    try:
        return await service.update_price_list(db, id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

@pricelist_router.post("/{id}/items", response_model=PriceListItemResponse, status_code=status.HTTP_201_CREATED)
async def add_price_item_route(id: int, data: PriceListItemCreate, db: AsyncSession = Depends(get_db)):
    """Add price item"""
    try:
        return await service.add_price_item(db, id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

@pricelist_router.get("/{id}/items", response_model=PaginatedResponse[PriceListItemResponse])
async def list_price_items_route(
    id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List price items"""
    query = select(PriceListItem).where(PriceListItem.price_list_id == id)
    total_count = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    total_pages = (total_count + page_size - 1) // page_size if total_count else 0

    return PaginatedResponse(
        items=[item for item in items],
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@pricelist_router.post("/{id}/duplicate", response_model=PriceListResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_price_list_route(id: int, data: DuplicateRequest, db: AsyncSession = Depends(get_db)):
    """Duplicate price list"""
    try:
        return await service.duplicate_price_list(db, id, data.new_code, data.new_name)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@pricing_router.post("/lookup", response_model=PriceLookupResponse)
async def lookup_price_route(request: PriceLookupRequest, db: AsyncSession = Depends(get_db)):
    """Lookup price"""
    try:
        return await service.get_price(db, request)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@pricing_router.post("/best-price", response_model=PriceLookupResponse)
async def best_price_route(request: PriceLookupRequest, db: AsyncSession = Depends(get_db)):
    """Find best price"""
    try:
        return await service.get_best_price(db, request)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

router.include_router(pricelist_router)
router.include_router(pricing_router)

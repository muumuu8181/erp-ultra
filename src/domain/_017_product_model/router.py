from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database.engine import get_db
from shared.types import PaginatedResponse
from src.domain._017_product_model import service
from src.domain._017_product_model.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductSearchFilter
)
from shared.types import BaseSchema

class PricingUpdate(BaseSchema):
    standard_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None

router = APIRouter(prefix="/api/v1/products", tags=["products"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Create a new product."""
    return await service.create_product(db, data)

@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def list_products_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    supplier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List products (paginated)."""
    return await service.list_products(db, page=page, page_size=page_size, category=category, is_active=is_active, supplier_id=supplier_id)

@router.get("/categories", response_model=List[ProductCategoryResponse])
async def list_categories_endpoint(
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List categories."""
    return await service.list_categories(db, parent_id=parent_id, is_active=is_active)

@router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category_endpoint(data: ProductCategoryCreate, db: AsyncSession = Depends(get_db)):
    """Create a product category."""
    return await service.create_category(db, data)

@router.get("/search", response_model=PaginatedResponse[ProductResponse])
async def search_products_endpoint(
    q: Optional[str] = None,
    category: Optional[str] = None,
    sub_category: Optional[str] = None,
    is_active: Optional[bool] = None,
    tax_type: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    supplier_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search products with filters."""
    filters = ProductSearchFilter(
        query=q,
        category=category,
        sub_category=sub_category,
        is_active=is_active,
        tax_type=tax_type,
        min_price=min_price,
        max_price=max_price,
        supplier_id=supplier_id
    )
    return await service.search_products(db, filters, page=page, page_size=page_size)

@router.get("/{id}", response_model=ProductResponse)
async def get_product_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    """Get product by ID."""
    return await service.get_product(db, id)

@router.put("/{id}", response_model=ProductResponse)
async def update_product_endpoint(id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    """Update product."""
    return await service.update_product(db, id, data)

@router.delete("/{id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def deactivate_product_endpoint(id: int, db: AsyncSession = Depends(get_db)):
    """Deactivate product (soft delete)."""
    return await service.deactivate_product(db, id)

@router.put("/{id}/pricing", response_model=ProductResponse)
async def update_product_pricing_endpoint(id: int, data: PricingUpdate, db: AsyncSession = Depends(get_db)):
    """Update product pricing."""
    return await service.update_pricing(db, id, standard_price=data.standard_price, cost_price=data.cost_price)

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from shared.types import PaginatedResponse
from shared.errors import DuplicateError, NotFoundError, ValidationError, BusinessRuleError
from src.foundation._001_database.engine import get_db

from src.domain._016_customer_model.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerContactCreate,
    CustomerContactResponse
)
from src.domain._016_customer_model.service import (
    create_customer,
    update_customer,
    get_customer,
    list_customers,
    deactivate_customer,
    add_contact,
    remove_contact,
    search_customers
)


router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def api_create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    """Create a new customer."""
    try:
        customer = await create_customer(db, data)
        return customer
    except (DuplicateError, ValidationError) as e:
        if isinstance(e, ValidationError):
            raise HTTPException(status_code=422, detail=e.message)
        if isinstance(e, DuplicateError):
            raise HTTPException(status_code=409, detail=e.message)
        raise


@router.get("/", response_model=CustomerListResponse)
async def api_list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List customers with pagination and optional filters."""
    result = await list_customers(db, page, page_size, is_active, type)
    return result


@router.get("/search", response_model=CustomerListResponse)
async def api_search_customers(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search customers by query param."""
    result = await search_customers(db, q, page, page_size)
    return result


@router.get("/{id}", response_model=CustomerResponse)
async def api_get_customer(id: int, db: AsyncSession = Depends(get_db)):
    """Get customer by ID."""
    try:
        return await get_customer(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.put("/{id}", response_model=CustomerResponse)
async def api_update_customer(id: int, data: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    """Update customer."""
    try:
        return await update_customer(db, id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)


@router.delete("/{id}", response_model=CustomerResponse)
async def api_delete_customer(id: int, db: AsyncSession = Depends(get_db)):
    """Deactivate customer (soft delete)."""
    try:
        return await deactivate_customer(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/{id}/contacts", response_model=CustomerContactResponse, status_code=status.HTTP_201_CREATED)
async def api_add_contact(id: int, data: CustomerContactCreate, db: AsyncSession = Depends(get_db)):
    """Add a contact to customer."""
    try:
        return await add_contact(db, id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/{id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_remove_contact(id: int, contact_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a contact."""
    try:
        await remove_contact(db, id, contact_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=e.message)

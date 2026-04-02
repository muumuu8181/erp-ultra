import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.types import PaginatedResponse
from shared.schema import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

# Assuming foundation db module has get_db,
# for independent module, we can define a stub or import if it exists.
try:
    from foundation._001_database.engine import get_db
except ImportError:
    # Fallback for standalone testing if needed
    async def get_db():
        yield None

from . import service
from .schemas import ContactCreate, ContactUpdate, ContactResponse

router = APIRouter(prefix="/api/v1/contacts", tags=["Contacts"])

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    """Create a new contact."""
    contact = await service.create_contact(db, data)
    return ContactResponse.model_validate(contact)

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    """Get a contact by ID."""
    contact = await service.get_contact(db, contact_id)
    return ContactResponse.model_validate(contact)

@router.get("/", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    customer_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[ContactResponse]:
    """List contacts with pagination."""
    skip = (page - 1) * page_size
    items, total = await service.list_contacts(
        db, skip=skip, limit=page_size,
        customer_id=customer_id, supplier_id=supplier_id
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=[ContactResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    """Update a contact."""
    contact = await service.update_contact(db, contact_id, data)
    return ContactResponse.model_validate(contact)

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a contact."""
    await service.delete_contact(db, contact_id)

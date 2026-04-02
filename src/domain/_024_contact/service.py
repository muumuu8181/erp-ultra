from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared.errors import NotFoundError
from .models import Contact
from .schemas import ContactCreate, ContactUpdate
from .validators import validate_phone_number

async def create_contact(db: AsyncSession, data: ContactCreate) -> Contact:
    """
    Create a new contact.
    """
    validate_phone_number(data.phone)
    validate_phone_number(data.mobile)

    contact = Contact(**data.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

async def get_contact(db: AsyncSession, contact_id: int) -> Contact:
    """
    Retrieve a contact by ID.
    Raises NotFoundError if not found.
    """
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise NotFoundError(f"Contact with ID {contact_id} not found")
    return contact

async def list_contacts(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    customer_id: Optional[int] = None,
    supplier_id: Optional[int] = None
) -> tuple[Sequence[Contact], int]:
    """
    List contacts with optional filtering by customer_id or supplier_id.
    Returns a tuple of (items, total_count).
    """
    query = select(Contact)
    if customer_id is not None:
        query = query.where(Contact.customer_id == customer_id)
    if supplier_id is not None:
        query = query.where(Contact.supplier_id == supplier_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get items
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return items, total

async def update_contact(db: AsyncSession, contact_id: int, data: ContactUpdate) -> Contact:
    """
    Update an existing contact.
    Raises NotFoundError if not found.
    """
    contact = await get_contact(db, contact_id)

    update_data = data.model_dump(exclude_unset=True)

    if "phone" in update_data:
        validate_phone_number(update_data["phone"])
    if "mobile" in update_data:
        validate_phone_number(update_data["mobile"])

    for key, value in update_data.items():
        setattr(contact, key, value)

    await db.commit()
    await db.refresh(contact)
    return contact

async def delete_contact(db: AsyncSession, contact_id: int) -> None:
    """
    Delete a contact by ID.
    Raises NotFoundError if not found.
    """
    contact = await get_contact(db, contact_id)
    await db.delete(contact)
    await db.commit()

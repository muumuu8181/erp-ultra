from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError

from shared.errors import DuplicateError, NotFoundError, BusinessRuleError
from shared.types import PaginatedResponse
from src.domain._016_customer_model.models import Customer, CustomerContact
from src.domain._016_customer_model.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerContactCreate,
)
from src.domain._016_customer_model.validators import validate_customer_create, validate_customer_update


async def create_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    """Create a new customer. Validates code uniqueness and format."""
    validate_customer_create(data)

    existing = await db.scalar(select(Customer).where(Customer.code == data.code))
    if existing:
        raise DuplicateError("Customer", data.code)

    customer = Customer(**data.model_dump())
    db.add(customer)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("Customer", data.code)

    stmt = select(Customer).where(Customer.id == customer.id)
    from sqlalchemy.orm import selectinload
    stmt = stmt.options(selectinload(Customer.contacts))
    return await db.scalar(stmt)


async def update_customer(db: AsyncSession, customer_id: int, data: CustomerUpdate) -> Customer:
    """Update an existing customer by ID."""
    validate_customer_update(data)

    customer = await db.scalar(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    if not customer:
        raise NotFoundError("Customer", str(customer_id))

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(customer, key, value)

    await db.commit()
    stmt = select(Customer).where(Customer.id == customer.id)
    from sqlalchemy.orm import selectinload
    stmt = stmt.options(selectinload(Customer.contacts))
    return await db.scalar(stmt)


async def get_customer(db: AsyncSession, customer_id: int) -> Customer:
    """Get a single customer by ID, including contacts."""
    stmt = select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False)
    from sqlalchemy.orm import selectinload
    stmt = stmt.options(selectinload(Customer.contacts))
    customer = await db.scalar(stmt)
    if not customer:
        raise NotFoundError("Customer", str(customer_id))
    return customer


async def list_customers(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
    customer_type: str | None = None
) -> PaginatedResponse:
    """List customers with pagination and optional filters."""
    stmt = select(Customer).where(Customer.is_deleted == False)

    if is_active is not None:
        stmt = stmt.where(Customer.is_active == is_active)
    if customer_type is not None:
        stmt = stmt.where(Customer.type == customer_type)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt) or 0

    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    from sqlalchemy.orm import selectinload
    stmt = stmt.options(selectinload(Customer.contacts))

    result = await db.scalars(stmt)
    items = list(result.all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def deactivate_customer(db: AsyncSession, customer_id: int) -> Customer:
    """Soft-delete / deactivate a customer. Sets is_active=False."""
    customer = await db.scalar(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    if not customer:
        raise NotFoundError("Customer", str(customer_id))

    customer.is_active = False
    customer.is_deleted = True
    from datetime import datetime, timezone
    customer.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    stmt = select(Customer).where(Customer.id == customer.id)
    from sqlalchemy.orm import selectinload
    stmt = stmt.options(selectinload(Customer.contacts))
    return await db.scalar(stmt)


async def add_contact(db: AsyncSession, customer_id: int, data: CustomerContactCreate) -> CustomerContact:
    """Add a contact to a customer."""
    customer = await db.scalar(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    if not customer:
        raise NotFoundError("Customer", str(customer_id))

    if data.is_primary:
        # Demote existing primary contact
        stmt = select(CustomerContact).where(CustomerContact.customer_id == customer_id, CustomerContact.is_primary == True)
        existing_primaries = await db.scalars(stmt)
        for c in existing_primaries.all():
            c.is_primary = False

    contact = CustomerContact(customer_id=customer_id, **data.model_dump())
    db.add(contact)
    await db.commit()

    # Return it explicitly after flush so it has ID, avoiding greenlet issues
    await db.refresh(contact)
    return contact


async def remove_contact(db: AsyncSession, customer_id: int, contact_id: int) -> None:
    """Remove a contact from a customer."""
    customer = await db.scalar(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    if not customer:
        raise NotFoundError("Customer", str(customer_id))

    contact = await db.scalar(select(CustomerContact).where(CustomerContact.id == contact_id))
    if not contact:
        raise NotFoundError("CustomerContact", str(contact_id))

    if contact.customer_id != customer_id:
        raise BusinessRuleError("Contact does not belong to the specified customer.")

    await db.delete(contact)
    await db.commit()


async def search_customers(db: AsyncSession, query: str, page: int = 1, page_size: int = 20) -> PaginatedResponse:
    """Search customers by name, name_kana, code, or email using ILIKE."""
    stmt = select(Customer).where(Customer.is_deleted == False)

    if query:
        search_pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Customer.name.ilike(search_pattern),
                Customer.name_kana.ilike(search_pattern),
                Customer.code.ilike(search_pattern),
                Customer.email.ilike(search_pattern)
            )
        )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt) or 0

    stmt = stmt.limit(page_size).offset((page - 1) * page_size)
    from sqlalchemy.orm import selectinload
    stmt = stmt.options(selectinload(Customer.contacts))

    result = await db.scalars(stmt)
    items = list(result.all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

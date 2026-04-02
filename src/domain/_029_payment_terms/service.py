"""
Service layer for Payment Terms module.
"""
from typing import Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from shared.errors import NotFoundError, DuplicateError
from src.domain._029_payment_terms.models import PaymentTerm
from src.domain._029_payment_terms.schemas import PaymentTermCreate, PaymentTermUpdate
from src.domain._029_payment_terms.validators import validate_payment_term_create, validate_payment_term_update


async def get_payment_term(db: AsyncSession, term_id: int) -> PaymentTerm:
    """
    Retrieve a Payment Term by its ID.

    Args:
        db: AsyncSession
        term_id: ID of the Payment Term

    Returns:
        PaymentTerm object

    Raises:
        NotFoundError: If the Payment Term is not found
    """
    result = await db.execute(select(PaymentTerm).where(PaymentTerm.id == term_id))
    term = result.scalar_one_or_none()

    if not term:
        raise NotFoundError("PaymentTerm", str(term_id))

    return term


async def list_payment_terms(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> tuple[Sequence[PaymentTerm], int]:
    """
    List Payment Terms with pagination.

    Args:
        db: AsyncSession
        skip: Offset for pagination
        limit: Limit for pagination
        is_active: Optional filter by active status

    Returns:
        Tuple containing a list of PaymentTerm objects and total count
    """
    query = select(PaymentTerm)
    count_query = select(func.count()).select_from(PaymentTerm)

    if is_active is not None:
        query = query.where(PaymentTerm.is_active == is_active)
        count_query = count_query.where(PaymentTerm.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)

    return result.scalars().all(), total


async def create_payment_term(db: AsyncSession, data: PaymentTermCreate) -> PaymentTerm:
    """
    Create a new Payment Term.

    Args:
        db: AsyncSession
        data: PaymentTermCreate schema containing creation data

    Returns:
        Created PaymentTerm object

    Raises:
        ValidationError: If the input data is invalid
        DuplicateError: If a Payment Term with the same code already exists
    """
    validate_payment_term_create(data)

    # Check for duplicate code
    existing_result = await db.execute(select(PaymentTerm).where(PaymentTerm.code == data.code))
    if existing_result.scalar_one_or_none():
        raise DuplicateError("PaymentTerm", data.code)

    term = PaymentTerm(**data.model_dump())
    db.add(term)

    try:
        await db.commit()
        await db.refresh(term)
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("PaymentTerm", data.code)

    return term


async def update_payment_term(db: AsyncSession, term_id: int, data: PaymentTermUpdate) -> PaymentTerm:
    """
    Update an existing Payment Term.

    Args:
        db: AsyncSession
        term_id: ID of the Payment Term to update
        data: PaymentTermUpdate schema containing update data

    Returns:
        Updated PaymentTerm object

    Raises:
        NotFoundError: If the Payment Term is not found
        ValidationError: If the update data is invalid
        DuplicateError: If updating to a code that already exists
    """
    term = await get_payment_term(db, term_id)

    validate_payment_term_update(data)

    update_data = data.model_dump(exclude_unset=True)

    if "code" in update_data and update_data["code"] != term.code:
        # Check for duplicate code if code is being updated
        existing_result = await db.execute(select(PaymentTerm).where(PaymentTerm.code == update_data["code"]))
        if existing_result.scalar_one_or_none():
            raise DuplicateError("PaymentTerm", update_data["code"])

    for key, value in update_data.items():
        setattr(term, key, value)

    try:
        await db.commit()
        await db.refresh(term)
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("PaymentTerm", update_data.get("code", term.code))

    return term


async def delete_payment_term(db: AsyncSession, term_id: int) -> bool:
    """
    Delete a Payment Term.

    Args:
        db: AsyncSession
        term_id: ID of the Payment Term to delete

    Returns:
        True if successfully deleted

    Raises:
        NotFoundError: If the Payment Term is not found
    """
    term = await get_payment_term(db, term_id)

    await db.delete(term)
    await db.commit()

    return True

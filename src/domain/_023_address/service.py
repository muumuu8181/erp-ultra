"""
Service layer for Address Book module.
"""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError
from .models import Address
from .schemas import AddressCreate, AddressUpdate


from .validators import validate_address_create, validate_address_update

async def create_address(db: AsyncSession, schema: AddressCreate) -> Address:
    """
    Create a new address.

    Args:
        db: The database session.
        schema: The data to create the address.

    Returns:
        The created address.
    """
    validate_address_create(schema)
    address = Address(**schema.model_dump())
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


async def get_address(db: AsyncSession, address_id: int) -> Address:
    """
    Retrieve an address by its ID.

    Args:
        db: The database session.
        address_id: The ID of the address.

    Returns:
        The retrieved address.

    Raises:
        NotFoundError: If the address does not exist.
    """
    address = await db.get(Address, address_id)
    if not address:
        raise NotFoundError(resource="Address", resource_id=str(address_id))
    return address


async def update_address(db: AsyncSession, address_id: int, schema: AddressUpdate) -> Address:
    """
    Update an existing address.

    Args:
        db: The database session.
        address_id: The ID of the address.
        schema: The data to update.

    Returns:
        The updated address.

    Raises:
        NotFoundError: If the address does not exist.
    """
    validate_address_update(schema)
    address = await get_address(db, address_id)

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(address, key, value)

    await db.commit()
    await db.refresh(address)
    return address


async def delete_address(db: AsyncSession, address_id: int) -> None:
    """
    Delete an address by its ID.

    Args:
        db: The database session.
        address_id: The ID of the address.

    Raises:
        NotFoundError: If the address does not exist.
    """
    address = await get_address(db, address_id)
    await db.delete(address)
    await db.commit()


async def list_addresses(db: AsyncSession, skip: int = 0, limit: int = 50) -> Sequence[Address]:
    """
    List addresses with pagination.

    Args:
        db: The database session.
        skip: The number of records to skip.
        limit: The maximum number of records to return.

    Returns:
        A list of addresses.
    """
    stmt = select(Address).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

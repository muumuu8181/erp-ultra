import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from shared.errors import NotFoundError, ValidationError
from src.domain._023_address.schemas import AddressCreate, AddressUpdate
from src.domain._023_address.service import (
    create_address,
    get_address,
    update_address,
    delete_address,
    list_addresses,
)

@pytest.mark.asyncio
async def test_create_address(db_session: AsyncSession) -> None:
    schema = AddressCreate(
        postal_code="123-4567",
        prefecture="Tokyo",
        city="Shinjuku-ku",
        street="1-1-1",
        building="Tokyo Govt Bldg"
    )

    address = await create_address(db_session, schema)

    assert address.id is not None
    assert address.postal_code == "123-4567"
    assert address.city == "Shinjuku-ku"

@pytest.mark.asyncio
async def test_create_address_invalid_postal_code(db_session: AsyncSession) -> None:
    schema = AddressCreate(
        postal_code="12-4567", # Invalid format
        prefecture="Tokyo",
        city="Shinjuku-ku",
        street="1-1-1"
    )

    with pytest.raises(ValidationError):
        await create_address(db_session, schema)

@pytest.mark.asyncio
async def test_get_address(db_session: AsyncSession) -> None:
    schema = AddressCreate(
        postal_code="123-4567",
        prefecture="Tokyo",
        city="Shinjuku-ku",
        street="1-1-1"
    )
    created = await create_address(db_session, schema)

    retrieved = await get_address(db_session, created.id)
    assert retrieved.id == created.id
    assert retrieved.postal_code == "123-4567"

@pytest.mark.asyncio
async def test_get_address_not_found(db_session: AsyncSession) -> None:
    with pytest.raises(NotFoundError):
        await get_address(db_session, 9999)

@pytest.mark.asyncio
async def test_update_address(db_session: AsyncSession) -> None:
    schema = AddressCreate(
        postal_code="123-4567",
        prefecture="Tokyo",
        city="Shinjuku-ku",
        street="1-1-1"
    )
    created = await create_address(db_session, schema)

    update_schema = AddressUpdate(city="Shibuya-ku", street="2-2-2")
    updated = await update_address(db_session, created.id, update_schema)

    assert updated.id == created.id
    assert updated.city == "Shibuya-ku"
    assert updated.street == "2-2-2"
    assert updated.prefecture == "Tokyo"  # Unchanged

@pytest.mark.asyncio
async def test_delete_address(db_session: AsyncSession) -> None:
    schema = AddressCreate(
        postal_code="123-4567",
        prefecture="Tokyo",
        city="Shinjuku-ku",
        street="1-1-1"
    )
    created = await create_address(db_session, schema)

    await delete_address(db_session, created.id)

    with pytest.raises(NotFoundError):
        await get_address(db_session, created.id)

@pytest.mark.asyncio
async def test_list_addresses(db_session: AsyncSession) -> None:
    for i in range(5):
        schema = AddressCreate(
            postal_code=f"123-456{i}",
            prefecture="Tokyo",
            city="City",
            street="Street"
        )
        await create_address(db_session, schema)

    addresses = await list_addresses(db_session, skip=0, limit=10)
    assert len(addresses) == 5

    addresses_page2 = await list_addresses(db_session, skip=2, limit=2)
    assert len(addresses_page2) == 2

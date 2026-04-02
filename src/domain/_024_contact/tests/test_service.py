import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from domain._024_contact import service
from domain._024_contact.schemas import ContactCreate, ContactUpdate
from domain._024_contact.models import Contact
from shared.errors import NotFoundError, ValidationError

@pytest.mark.asyncio
async def test_create_contact(db_session: AsyncSession):
    data = ContactCreate(first_name="Alice", last_name="Smith", phone="+1234")
    contact = await service.create_contact(db_session, data)
    assert contact.id is not None
    assert contact.first_name == "Alice"

@pytest.mark.asyncio
async def test_create_contact_invalid_phone(db_session: AsyncSession):
    data = ContactCreate(first_name="Alice", last_name="Smith", phone="invalid")
    with pytest.raises(ValidationError):
        await service.create_contact(db_session, data)

@pytest.mark.asyncio
async def test_get_contact(db_session: AsyncSession):
    data = ContactCreate(first_name="Bob", last_name="Brown")
    created = await service.create_contact(db_session, data)

    fetched = await service.get_contact(db_session, created.id)
    assert fetched.id == created.id

@pytest.mark.asyncio
async def test_get_contact_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await service.get_contact(db_session, 9999)

@pytest.mark.asyncio
async def test_list_contacts(db_session: AsyncSession):
    await service.create_contact(db_session, ContactCreate(first_name="C1", last_name="L1", customer_id=1))
    await service.create_contact(db_session, ContactCreate(first_name="C2", last_name="L2", customer_id=1))
    await service.create_contact(db_session, ContactCreate(first_name="C3", last_name="L3", customer_id=2))

    items, total = await service.list_contacts(db_session, customer_id=1)
    assert total == 2
    assert len(items) == 2

@pytest.mark.asyncio
async def test_update_contact(db_session: AsyncSession):
    created = await service.create_contact(db_session, ContactCreate(first_name="Old", last_name="Name"))

    updated = await service.update_contact(db_session, created.id, ContactUpdate(first_name="New"))
    assert updated.first_name == "New"
    assert updated.last_name == "Name"

@pytest.mark.asyncio
async def test_delete_contact(db_session: AsyncSession):
    created = await service.create_contact(db_session, ContactCreate(first_name="Del", last_name="Me"))

    await service.delete_contact(db_session, created.id)

    with pytest.raises(NotFoundError):
        await service.get_contact(db_session, created.id)

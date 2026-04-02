import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from shared.errors import DuplicateError, NotFoundError
from src.domain._016_customer_model.schemas import CustomerCreate, CustomerUpdate, CustomerContactCreate
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

pytestmark = pytest.mark.asyncio

async def test_create_customer(db_session: AsyncSession):
    data = CustomerCreate(
        code="CUS-00001",
        name="Test Customer",
        type="corporate",
        tax_type="standard_10"
    )
    customer = await create_customer(db_session, data)
    assert customer.id is not None
    assert customer.code == "CUS-00001"

async def test_create_duplicate_code(db_session: AsyncSession):
    data = CustomerCreate(
        code="CUS-00001",
        name="Test Customer 1",
        type="corporate",
        tax_type="standard_10"
    )
    await create_customer(db_session, data)

    data2 = CustomerCreate(
        code="CUS-00001",
        name="Test Customer 2",
        type="corporate",
        tax_type="standard_10"
    )
    with pytest.raises(DuplicateError):
        await create_customer(db_session, data2)

async def test_update_customer(db_session: AsyncSession):
    data = CustomerCreate(
        code="CUS-00002",
        name="Update Customer",
        type="corporate",
        tax_type="standard_10"
    )
    customer = await create_customer(db_session, data)

    update_data = CustomerUpdate(name="Updated Name", type="individual")
    updated = await update_customer(db_session, customer.id, update_data)
    assert updated.name == "Updated Name"
    assert updated.type == "individual"

async def test_update_non_existent(db_session: AsyncSession):
    update_data = CustomerUpdate(name="Updated Name")
    with pytest.raises(NotFoundError):
        await update_customer(db_session, 9999, update_data)

async def test_get_customer(db_session: AsyncSession):
    data = CustomerCreate(
        code="CUS-00003",
        name="Get Customer",
        type="corporate",
        tax_type="standard_10"
    )
    customer = await create_customer(db_session, data)

    fetched = await get_customer(db_session, customer.id)
    assert fetched.id == customer.id

async def test_get_non_existent(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await get_customer(db_session, 9999)

async def test_list_customers(db_session: AsyncSession):
    for i in range(5):
        data = CustomerCreate(
            code=f"CUS-1000{i}",
            name=f"List Customer {i}",
            type="corporate",
            tax_type="standard_10"
        )
        await create_customer(db_session, data)

    result = await list_customers(db_session, page=1, page_size=2)
    assert result.total >= 5
    assert len(result.items) == 2
    assert result.page_size == 2

async def test_deactivate_customer(db_session: AsyncSession):
    data = CustomerCreate(
        code="CUS-00004",
        name="Deactivate Customer",
        type="corporate",
        tax_type="standard_10"
    )
    customer = await create_customer(db_session, data)

    deactivated = await deactivate_customer(db_session, customer.id)
    assert deactivated.is_active is False
    assert deactivated.is_deleted is True

    with pytest.raises(NotFoundError):
        await get_customer(db_session, customer.id)

async def test_add_and_remove_contact(db_session: AsyncSession):
    data = CustomerCreate(
        code="CUS-00005",
        name="Contact Customer",
        type="corporate",
        tax_type="standard_10"
    )
    customer = await create_customer(db_session, data)

    contact_data = CustomerContactCreate(
        name="Contact 1",
        is_primary=True
    )
    contact1 = await add_contact(db_session, customer.id, contact_data)
    assert contact1.is_primary is True

    contact_data2 = CustomerContactCreate(
        name="Contact 2",
        is_primary=True
    )
    contact2 = await add_contact(db_session, customer.id, contact_data2)
    assert contact2.is_primary is True

    # Demotion check
    from sqlalchemy import select
    from src.domain._016_customer_model.models import CustomerContact
    contact1_refreshed = await db_session.scalar(select(CustomerContact).where(CustomerContact.id == contact1.id))
    assert contact1_refreshed.is_primary is False

    await remove_contact(db_session, customer.id, contact1.id)
    with pytest.raises(NotFoundError):
        await remove_contact(db_session, customer.id, contact1.id)

async def test_search_customers(db_session: AsyncSession):
    data1 = CustomerCreate(code="CUS-S0001", name="Alpha Corp", type="corporate", tax_type="standard_10")
    data2 = CustomerCreate(code="CUS-S0002", name="Beta LLC", type="corporate", tax_type="standard_10")
    await create_customer(db_session, data1)
    await create_customer(db_session, data2)

    result = await search_customers(db_session, "Alpha")
    assert result.total == 1
    assert result.items[0].name == "Alpha Corp"

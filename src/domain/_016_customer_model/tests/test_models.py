import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from src.domain._016_customer_model.models import Customer, CustomerContact

pytestmark = pytest.mark.asyncio

async def test_create_customer(db_session: AsyncSession):
    customer = Customer(
        code="CUS-00001",
        name="Test Corp",
        type="corporate",
        tax_type="standard_10"
    )
    db_session.add(customer)
    await db_session.commit()

    saved = await db_session.scalar(select(Customer).where(Customer.code == "CUS-00001"))
    assert saved is not None
    assert saved.name == "Test Corp"
    assert saved.is_active is True
    assert saved.is_deleted is False


async def test_create_customer_with_contacts(db_session: AsyncSession):
    customer = Customer(
        code="CUS-00002",
        name="Another Corp",
        type="corporate",
        tax_type="standard_10"
    )
    contact = CustomerContact(
        name="John Doe",
        email="john@example.com",
        is_primary=True
    )
    customer.contacts.append(contact)
    db_session.add(customer)
    await db_session.commit()

    saved = await db_session.scalar(
        select(Customer)
        .where(Customer.code == "CUS-00002")
    )
    from sqlalchemy.orm import selectinload
    saved = await db_session.scalar(
        select(Customer)
        .options(selectinload(Customer.contacts))
        .where(Customer.code == "CUS-00002")
    )

    assert len(saved.contacts) == 1
    assert saved.contacts[0].name == "John Doe"

async def test_cascade_delete(db_session: AsyncSession):
    customer = Customer(
        code="CUS-00003",
        name="Delete Corp",
        type="corporate",
        tax_type="standard_10"
    )
    contact = CustomerContact(
        name="Jane Doe"
    )
    customer.contacts.append(contact)
    db_session.add(customer)
    await db_session.commit()

    await db_session.delete(customer)
    await db_session.commit()

    contacts = await db_session.scalars(select(CustomerContact))
    assert len(contacts.all()) == 0

async def test_unique_constraint(db_session: AsyncSession):
    c1 = Customer(code="CUS-DUP", name="A", type="corporate", tax_type="standard_10")
    db_session.add(c1)
    await db_session.commit()

    c2 = Customer(code="CUS-DUP", name="B", type="corporate", tax_type="standard_10")
    db_session.add(c2)
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        await db_session.commit()

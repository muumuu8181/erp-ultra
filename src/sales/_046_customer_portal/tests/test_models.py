import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from src.sales._046_customer_portal.models import PortalUser, PortalSession

@pytest.mark.asyncio
async def test_portal_user_creation(db: AsyncSession):
    user = PortalUser(
        customer_code="CUST001",
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_pwd",
    )
    db.add(user)
    await db.commit()

    assert user.id is not None
    assert user.is_active is True
    assert user.created_at is not None

@pytest.mark.asyncio
async def test_portal_session_creation(db: AsyncSession):
    user = PortalUser(
        customer_code="CUST002",
        username="testuser2",
        email="test2@example.com",
        hashed_password="hashed_pwd",
    )
    db.add(user)
    await db.flush()

    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
    session = PortalSession(
        user_id=user.id,
        token="some_token",
        ip_address="127.0.0.1",
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()

    assert session.id is not None
    assert session.user.id == user.id

@pytest.mark.asyncio
async def test_portal_user_unique_username(db: AsyncSession):
    user1 = PortalUser(
        customer_code="CUST003",
        username="duplicate_user",
        email="test3@example.com",
        hashed_password="hashed_pwd",
    )
    user2 = PortalUser(
        customer_code="CUST004",
        username="duplicate_user",
        email="test4@example.com",
        hashed_password="hashed_pwd",
    )
    db.add(user1)
    db.add(user2)

    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

@pytest.mark.asyncio
async def test_portal_user_unique_email(db: AsyncSession):
    user1 = PortalUser(
        customer_code="CUST005",
        username="user5",
        email="duplicate@example.com",
        hashed_password="hashed_pwd",
    )
    user2 = PortalUser(
        customer_code="CUST006",
        username="user6",
        email="duplicate@example.com",
        hashed_password="hashed_pwd",
    )
    db.add(user1)
    db.add(user2)

    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

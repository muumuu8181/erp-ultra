import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext # type: ignore

from shared.errors import ValidationError, DuplicateError
from src.sales._046_customer_portal.validators import (
    validate_customer_code,
    validate_email_unique,
    validate_username_unique,
    validate_password_strength,
    validate_current_password,
    pwd_context
)
from src.sales._046_customer_portal.models import PortalUser

@pytest.mark.asyncio
async def test_validate_customer_code(db: AsyncSession):
    with pytest.raises(ValidationError):
        await validate_customer_code(db, "")

    # Should not raise
    await validate_customer_code(db, "CUST123")

@pytest.mark.asyncio
async def test_validate_email_unique(db: AsyncSession):
    user = PortalUser(
        customer_code="CUST001",
        username="user1",
        email="test@example.com",
        hashed_password="hash"
    )
    db.add(user)
    await db.commit()

    with pytest.raises(DuplicateError):
        await validate_email_unique(db, "test@example.com")

    # Should not raise
    await validate_email_unique(db, "new@example.com")

@pytest.mark.asyncio
async def test_validate_username_unique(db: AsyncSession):
    user = PortalUser(
        customer_code="CUST001",
        username="user1",
        email="test@example.com",
        hashed_password="hash"
    )
    db.add(user)
    await db.commit()

    with pytest.raises(DuplicateError):
        await validate_username_unique(db, "user1")

    # Should not raise
    await validate_username_unique(db, "user2")

def test_validate_password_strength():
    with pytest.raises(ValidationError):
        validate_password_strength("short")

    with pytest.raises(ValidationError):
        validate_password_strength("nouppercase1")

    with pytest.raises(ValidationError):
        validate_password_strength("NoDigitHere")

    # Should not raise
    validate_password_strength("Valid1Pass")

def test_validate_current_password():
    hashed = pwd_context.hash("Correct1Pass")

    with pytest.raises(ValidationError):
        validate_current_password(hashed, "Wrong1Pass")

    # Should not raise
    validate_current_password(hashed, "Correct1Pass")

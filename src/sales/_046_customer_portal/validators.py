"""
Validators for Customer Portal.
"""
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext # type: ignore

from shared.errors import ValidationError, DuplicateError
from .models import PortalUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def validate_customer_code(db: AsyncSession, customer_code: str) -> None:
    """
    Validates that a customer code exists.
    Stub implementation for now.
    """
    if not customer_code:
        raise ValidationError("Customer code is required", field="customer_code")
    # In a real implementation, we would check the customer master table here.


async def validate_email_unique(db: AsyncSession, email: str) -> None:
    """
    Validates that an email is unique across PortalUsers.
    """
    stmt = select(PortalUser).where(PortalUser.email == email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise DuplicateError("PortalUser", key=email)


async def validate_username_unique(db: AsyncSession, username: str) -> None:
    """
    Validates that a username is unique across PortalUsers.
    """
    stmt = select(PortalUser).where(PortalUser.username == username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise DuplicateError("PortalUser", key=username)


def validate_password_strength(password: str) -> None:
    """
    Validates password strength: min 8 chars, 1 upper, 1 digit.
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long", field="password")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter", field="password")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit", field="password")


def validate_current_password(hashed_password: str, current_password: str) -> None:
    """
    Validates that the current password matches the stored hash.
    """
    if not pwd_context.verify(current_password, hashed_password):
        raise ValidationError("Incorrect current password", field="current_password")

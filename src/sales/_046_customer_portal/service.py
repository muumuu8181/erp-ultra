"""
Service layer for Customer Portal.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError, NotFoundError
from shared.types import PaginatedResponse
from .models import PortalUser, PortalSession
from .schemas import (
    PortalRegistration,
    PortalLogin,
    PortalDashboardData,
    OrderHistoryResponse,
)
from .validators import (
    validate_customer_code,
    validate_email_unique,
    validate_username_unique,
    validate_password_strength,
    validate_current_password,
    pwd_context,
)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


async def register(db: AsyncSession, data: PortalRegistration) -> PortalUser:
    """Register a new customer portal user."""
    await validate_customer_code(db, data.customer_code)
    await validate_email_unique(db, data.email)
    await validate_username_unique(db, data.username)
    validate_password_strength(data.password)

    hashed_password = get_password_hash(data.password)

    user = PortalUser(
        customer_code=data.customer_code,
        username=data.username,
        email=data.email,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def login(db: AsyncSession, data: PortalLogin, ip_address: str) -> PortalSession:
    """Login and get a session token."""
    stmt = select(PortalUser).where(PortalUser.username == data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(data.password, user.hashed_password):
        raise ValidationError("Incorrect username or password", field="password")

    if not user.is_active:
        raise ValidationError("User account is inactive", field="username")

    user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)

    token = secrets.token_hex(32)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)

    session = PortalSession(
        user_id=user.id,
        token=token,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()
    return session


async def get_dashboard(db: AsyncSession, user_id: int) -> PortalDashboardData:
    """Get dashboard data for a user."""
    user = await db.get(PortalUser, user_id)
    if not user:
        raise NotFoundError("PortalUser", str(user_id))

    # Stub data
    return PortalDashboardData(
        customer_code=user.customer_code,
        recent_orders=[],
        outstanding_invoices=[],
        total_spend=Decimal("0.00"),
        outstanding_amount=Decimal("0.00"),
    )


async def get_order_history(db: AsyncSession, user_id: int, page: int, size: int) -> OrderHistoryResponse:
    """Get order history for a user."""
    user = await db.get(PortalUser, user_id)
    if not user:
        raise NotFoundError("PortalUser", str(user_id))

    # Stub data
    return OrderHistoryResponse(
        orders=[],
        total_count=0,
    )


async def get_invoice_history(db: AsyncSession, user_id: int, page: int, size: int) -> PaginatedResponse:
    """Get invoice history for a user."""
    user = await db.get(PortalUser, user_id)
    if not user:
        raise NotFoundError("PortalUser", str(user_id))

    # Stub data
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=size,
        total_pages=0,
    )


async def change_password(db: AsyncSession, user_id: int, current_password: str, new_password: str) -> bool:
    """Change user password."""
    user = await db.get(PortalUser, user_id)
    if not user:
        raise NotFoundError("PortalUser", str(user_id))

    validate_current_password(user.hashed_password, current_password)
    validate_password_strength(new_password)

    user.hashed_password = get_password_hash(new_password)
    await db.flush()
    return True


async def reset_password_request(db: AsyncSession, email: str) -> str:
    """Request a password reset. Stub implementation."""
    stmt = select(PortalUser).where(PortalUser.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("PortalUser", email)

    return str(uuid.uuid4())

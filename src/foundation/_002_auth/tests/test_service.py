import pytest
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from shared.types import Base
from shared.errors import DuplicateError, NotFoundError, BusinessRuleError, ValidationError
from src.foundation._002_auth.models import User, RefreshToken
from src.foundation._002_auth.schemas import UserCreate, UserLogin
from src.foundation._002_auth.service import (
    register_user,
    login,
    refresh_access_token,
    revoke_token,
    verify_token,
    get_current_user,
    hash_password,
    verify_password
)

@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_register_user_success(db_session: AsyncSession):
    data = UserCreate(username="newuser", email="new@example.com", password="Password1")
    user = await register_user(db_session, data)

    assert user.id is not None
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert verify_password("Password1", user.hashed_password)

@pytest.mark.asyncio
async def test_register_user_duplicate_username(db_session: AsyncSession):
    user = User(username="dupuser", email="first@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()

    data = UserCreate(username="dupuser", email="second@example.com", password="Password1")
    with pytest.raises(DuplicateError):
        await register_user(db_session, data)

@pytest.mark.asyncio
async def test_register_user_duplicate_email(db_session: AsyncSession):
    user = User(username="firstuser", email="dup@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()

    data = UserCreate(username="seconduser", email="dup@example.com", password="Password1")
    with pytest.raises(DuplicateError):
        await register_user(db_session, data)

@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession):
    user = User(
        username="loginuser",
        email="login@example.com",
        hashed_password=hash_password("Password1")
    )
    db_session.add(user)
    await db_session.commit()

    data = UserLogin(email="login@example.com", password="Password1")
    tokens = await login(db_session, data)

    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession):
    user = User(
        username="wrongpwuser",
        email="wrong@example.com",
        hashed_password=hash_password("Password1")
    )
    db_session.add(user)
    await db_session.commit()

    data = UserLogin(email="wrong@example.com", password="WrongPassword")
    with pytest.raises(ValidationError):
        await login(db_session, data)

@pytest.mark.asyncio
async def test_login_inactive_user(db_session: AsyncSession):
    user = User(
        username="inactiveuser",
        email="inactive@example.com",
        hashed_password=hash_password("Password1"),
        is_active=False
    )
    db_session.add(user)
    await db_session.commit()

    data = UserLogin(email="inactive@example.com", password="Password1")
    with pytest.raises(BusinessRuleError):
        await login(db_session, data)

@pytest.mark.asyncio
async def test_login_nonexistent_user(db_session: AsyncSession):
    data = UserLogin(email="notfound@example.com", password="Password1")
    with pytest.raises(NotFoundError):
        await login(db_session, data)

@pytest.mark.asyncio
async def test_refresh_access_token_success(db_session: AsyncSession):
    user = User(username="refuser", email="ref@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    token = RefreshToken(user_id=user.id, token="old_refresh_token", expires_at=expires_at)
    db_session.add(token)
    await db_session.commit()

    tokens = await refresh_access_token(db_session, "old_refresh_token")

    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.refresh_token != "old_refresh_token"

    await db_session.refresh(token)
    assert token.revoked_at is not None

@pytest.mark.asyncio
async def test_refresh_access_token_expired(db_session: AsyncSession):
    user = User(username="expuser", email="exp@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    token = RefreshToken(user_id=user.id, token="expired_token", expires_at=expires_at)
    db_session.add(token)
    await db_session.commit()

    with pytest.raises(ValidationError):
        await refresh_access_token(db_session, "expired_token")

@pytest.mark.asyncio
async def test_refresh_access_token_revoked(db_session: AsyncSession):
    user = User(username="revuser", email="rev@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    token = RefreshToken(
        user_id=user.id,
        token="revoked_token",
        expires_at=expires_at,
        revoked_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(token)
    await db_session.commit()

    with pytest.raises(ValidationError):
        await refresh_access_token(db_session, "revoked_token")

@pytest.mark.asyncio
async def test_revoke_token_success(db_session: AsyncSession):
    user = User(username="logoutuser", email="logout@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    token = RefreshToken(user_id=user.id, token="token_to_revoke", expires_at=expires_at)
    db_session.add(token)
    await db_session.commit()

    await revoke_token(db_session, "token_to_revoke")
    await db_session.refresh(token)
    assert token.revoked_at is not None

@pytest.mark.asyncio
async def test_verify_token_invalid():
    with pytest.raises(ValidationError):
        await verify_token("invalid.token.string")

@pytest.mark.asyncio
async def test_get_current_user_success(db_session: AsyncSession):
    user = User(username="currentuser", email="current@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    from src.foundation._002_auth.service import create_access_token
    token = create_access_token(user.id)

    current = await get_current_user(db_session, token)
    assert current.id == user.id

@pytest.mark.asyncio
async def test_get_current_user_not_found(db_session: AsyncSession):
    from src.foundation._002_auth.service import create_access_token
    token = create_access_token(9999)

    with pytest.raises(NotFoundError):
        await get_current_user(db_session, token)

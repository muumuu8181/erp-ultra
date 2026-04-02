import pytest
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from shared.types import Base
from src.foundation._002_auth.models import User, RefreshToken

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
async def test_user_model_creation(db_session: AsyncSession):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_pw_123"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.role == "user"
    assert user.created_at is not None
    assert user.updated_at is not None

@pytest.mark.asyncio
async def test_refresh_token_model_creation(db_session: AsyncSession):
    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password="hashed_pw_123"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    token = RefreshToken(
        user_id=user.id,
        token="some_random_token_string",
        expires_at=expires_at
    )
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)

    assert token.id is not None
    assert token.user_id == user.id
    assert token.token == "some_random_token_string"
    assert token.expires_at == expires_at
    assert token.revoked_at is None
    assert token.created_at is not None

@pytest.mark.asyncio
async def test_user_refresh_token_relationship(db_session: AsyncSession):
    user = User(
        username="testuser3",
        email="test3@example.com",
        hashed_password="hashed_pw_123"
    )
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    token1 = RefreshToken(token="token1", expires_at=expires_at)
    token2 = RefreshToken(token="token2", expires_at=expires_at)

    user.refresh_tokens = [token1, token2]
    db_session.add(user)
    await db_session.commit()

    # Needs to eagerly load or execute async statement for relationships
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db_session.execute(select(User).where(User.id == user.id).options(selectinload(User.refresh_tokens)))
    loaded_user = result.scalar_one()

    assert len(loaded_user.refresh_tokens) == 2
    assert token1.user_id == user.id
    assert token2.user_id == user.id

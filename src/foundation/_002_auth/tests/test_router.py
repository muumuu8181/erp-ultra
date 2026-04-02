import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import FastAPI

from shared.types import Base
from src.foundation._001_database.engine import get_db
from src.foundation._002_auth.router import router
from src.foundation._002_auth.models import User, RefreshToken
from src.foundation._002_auth.service import hash_password, create_access_token, create_refresh_token_value

# Create test app
app = FastAPI()
app.include_router(router)

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

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_register_endpoint_success(client: AsyncClient):
    payload = {
        "username": "apiuser",
        "email": "api@example.com",
        "password": "StrongPassword1"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "apiuser"
    assert data["email"] == "api@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_register_endpoint_duplicate(client: AsyncClient, db_session: AsyncSession):
    user = User(username="dupapi", email="dupapi@example.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()

    payload = {
        "username": "dupapi",
        "email": "newapi@example.com",
        "password": "StrongPassword1"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_login_endpoint_success(client: AsyncClient, db_session: AsyncSession):
    user = User(username="loginapi", email="loginapi@example.com", hashed_password=hash_password("StrongPassword1"))
    db_session.add(user)
    await db_session.commit()

    payload = {
        "email": "loginapi@example.com",
        "password": "StrongPassword1"
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_endpoint_invalid(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "nonexistent@example.com",
        "password": "StrongPassword1"
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_refresh_endpoint_success(client: AsyncClient, db_session: AsyncSession):
    user = User(username="refapi", email="refapi@example.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    refresh_str = create_refresh_token_value()
    token = RefreshToken(
        user_id=user.id,
        token=refresh_str,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    )
    db_session.add(token)
    await db_session.commit()

    payload = {"refresh_token": refresh_str}
    response = await client.post("/api/v1/auth/refresh", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_logout_endpoint_success(client: AsyncClient, db_session: AsyncSession):
    user = User(username="logoutapi", email="logoutapi@example.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    refresh_str = create_refresh_token_value()
    token = RefreshToken(
        user_id=user.id,
        token=refresh_str,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    )
    db_session.add(token)
    await db_session.commit()

    payload = {"refresh_token": refresh_str}
    response = await client.post("/api/v1/auth/logout", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}

@pytest.mark.asyncio
async def test_me_endpoint_success(client: AsyncClient, db_session: AsyncSession):
    user = User(username="meapi", email="meapi@example.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    access_token = create_access_token(user.id)

    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meapi"
    assert data["email"] == "meapi@example.com"

@pytest.mark.asyncio
async def test_me_endpoint_no_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_me_endpoint_invalid_token(client: AsyncClient):
    headers = {"Authorization": "Bearer invalid.token.string"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401

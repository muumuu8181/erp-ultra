import os
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._002_auth.models import User, RefreshToken
from src.foundation._002_auth.schemas import UserCreate, UserLogin, TokenPair
from src.foundation._002_auth.validators import (
    validate_password_strength,
    validate_email_format,
    validate_username_format,
)
from shared.errors import NotFoundError, ValidationError, DuplicateError, BusinessRuleError

# --- JWT Configuration ---
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "erp-ultra-dev-secret-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE: timedelta = timedelta(minutes=30)
REFRESH_TOKEN_EXPIRE: timedelta = timedelta(days=7)

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plain password."""
    # passlib bcrypt has a 72 character limit. Truncate to avoid errors.
    # Note: in a real production system we might use a different hashing algorithm (e.g. argon2)
    # or pre-hash with SHA256, but for this constraint we truncate to 72 bytes.
    pwd_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(pwd_bytes.decode('utf-8', 'ignore'))

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against the hash."""
    plain_bytes = plain.encode('utf-8')[:72]
    return pwd_context.verify(plain_bytes.decode('utf-8', 'ignore'), hashed)

# --- Token Generation ---
def create_access_token(user_id: int) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": now + ACCESS_TOKEN_EXPIRE,
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token_value() -> str:
    """Create a unique refresh token string."""
    return str(uuid.uuid4())

# --- Service Functions ---

async def register_user(db: AsyncSession, data: UserCreate) -> User:
    """
    Register a new user.
    - Validate input using validators
    - Check for duplicate username/email (raise DuplicateError if exists)
    - Hash password with passlib bcrypt
    - Create User record in DB
    - Return the created User
    """
    validate_username_format(data.username)
    validate_email_format(data.email)
    validate_password_strength(data.password)

    # Check for duplicate email
    result_email = await db.execute(select(User).where(User.email == data.email))
    if result_email.scalar_one_or_none():
        raise DuplicateError("Email already registered")

    # Check for duplicate username
    result_username = await db.execute(select(User).where(User.username == data.username))
    if result_username.scalar_one_or_none():
        raise DuplicateError("Username already taken")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login(db: AsyncSession, data: UserLogin) -> TokenPair:
    """
    Authenticate user and return JWT token pair.
    - Look up user by email (raise NotFoundError if not found)
    - Verify password with bcrypt
    - Check is_active (raise BusinessRuleError if inactive)
    - Generate access token (30 min expiry) and refresh token (7 day expiry)
    - Store refresh token in DB
    - Return TokenPair
    """
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found")

    if not verify_password(data.password, user.hashed_password):
        raise ValidationError("Incorrect password")

    if not user.is_active:
        raise BusinessRuleError("User is inactive")

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token_value()

    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + REFRESH_TOKEN_EXPIRE
    )
    db.add(refresh_token)
    await db.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer"
    )

async def refresh_access_token(db: AsyncSession, refresh_token_str: str) -> TokenPair:
    """
    Exchange a valid refresh token for a new token pair.
    - Look up refresh token in DB
    - Check not expired and not revoked
    - Revoke the old refresh token
    - Generate new access + refresh token pair
    - Store new refresh token
    - Return TokenPair
    """
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token_str))
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        raise NotFoundError("Refresh token not found")

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if refresh_token.revoked_at is not None:
        raise ValidationError("Refresh token has been revoked")

    if refresh_token.expires_at < now:
        raise ValidationError("Refresh token has expired")

    # Revoke old token
    refresh_token.revoked_at = now

    user_id = refresh_token.user_id
    new_access_token = create_access_token(user_id)
    new_refresh_token_str = create_refresh_token_value()

    new_refresh_token = RefreshToken(
        user_id=user_id,
        token=new_refresh_token_str,
        expires_at=now + REFRESH_TOKEN_EXPIRE
    )
    db.add(new_refresh_token)
    await db.commit()

    return TokenPair(
        access_token=new_access_token,
        refresh_token=new_refresh_token_str,
        token_type="bearer"
    )

async def revoke_token(db: AsyncSession, refresh_token_str: str) -> None:
    """
    Revoke a refresh token (logout).
    - Look up token in DB (raise NotFoundError if not found)
    - Set revoked_at to now
    """
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token_str))
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        raise NotFoundError("Refresh token not found")

    refresh_token.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()

async def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT access token.
    - Decode using python-jose with HS256
    - Check expiry
    - Return the token payload dict
    - Raise ValidationError if token is invalid or expired
    Does NOT need db session (stateless JWT verification).
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValidationError("Could not validate credentials")

async def get_current_user(db: AsyncSession, token: str) -> User:
    """
    Get the current user from a JWT access token.
    - Verify the token
    - Extract user_id from payload sub claim
    - Fetch user from DB
    - Raise NotFoundError if user not found
    - Raise BusinessRuleError if user is inactive
    """
    payload = await verify_token(token)
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
         raise ValidationError("Could not validate credentials")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise ValidationError("Could not validate credentials")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User not found")

    if not user.is_active:
        raise BusinessRuleError("Inactive user")

    return user

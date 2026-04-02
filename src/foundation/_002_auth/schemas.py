from datetime import datetime
from shared.types import BaseSchema

class UserCreate(BaseSchema):
    """Schema for user registration."""
    username: str
    email: str
    password: str

class UserLogin(BaseSchema):
    """Schema for user login."""
    email: str
    password: str

class UserResponse(BaseSchema):
    """Schema returned after registration/login/user info."""
    id: int
    username: str
    email: str
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime

class TokenPair(BaseSchema):
    """JWT access + refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseSchema):
    """Schema for token refresh request."""
    refresh_token: str

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.foundation._001_database.engine import get_db
from src.foundation._002_auth.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenPair,
    RefreshTokenRequest
)
from src.foundation._002_auth.service import (
    register_user,
    login,
    refresh_access_token,
    revoke_token,
    get_current_user
)
from shared.errors import NotFoundError, ValidationError, DuplicateError, BusinessRuleError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await register_user(db, data)
        return user
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

@router.post("/login", response_model=TokenPair)
async def login_endpoint(data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        tokens = await login(db, data)
        return tokens
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        tokens = await refresh_access_token(db, data.refresh_token)
        return tokens
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/logout", response_model=Dict[str, str])
async def logout(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        await revoke_token(db, data.refresh_token)
        return {"message": "Logged out"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def me(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    try:
        user = await get_current_user(db, credentials.credentials)
        return user
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

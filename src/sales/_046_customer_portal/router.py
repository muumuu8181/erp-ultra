"""
Router for Customer Portal.
"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database import get_db
from shared.types import PaginatedResponse
from . import service
from .schemas import (
    PortalRegistration,
    PortalLogin,
    PortalUserResponse,
    PortalDashboardData,
    OrderHistoryResponse,
    ChangePasswordRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

router = APIRouter(prefix="/api/v1/portal", tags=["customer-portal"])

# In a real system, we'd have an auth dependency to get the current user ID
# from the session token. For these endpoints, we'll accept a mock `user_id`
# header for testing/stubbing.
def get_current_user_id(request: Request) -> int:
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return int(user_id)
    return 1 # Fallback for simple tests without auth setup


@router.post("/register", response_model=PortalUserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: PortalRegistration, db: AsyncSession = Depends(get_db)):
    """Register a new customer portal user."""
    user = await service.register(db, data)
    return user


@router.post("/login")
async def login(data: PortalLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Login and get a session token."""
    ip_address = request.client.host if request.client else "unknown"
    session = await service.login(db, data, ip_address)
    return {"token": session.token, "expires_at": session.expires_at}


@router.get("/dashboard", response_model=PortalDashboardData)
async def get_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Get customer dashboard data."""
    user_id = get_current_user_id(request)
    return await service.get_dashboard(db, user_id)


@router.get("/orders", response_model=OrderHistoryResponse)
async def get_orders(
    request: Request,
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get order history (paginated)."""
    user_id = get_current_user_id(request)
    return await service.get_order_history(db, user_id, page, size)


@router.get("/invoices", response_model=PaginatedResponse)
async def get_invoices(
    request: Request,
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get invoice history (paginated)."""
    user_id = get_current_user_id(request)
    return await service.get_invoice_history(db, user_id, page, size)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Change password."""
    user_id = get_current_user_id(request)
    success = await service.change_password(db, user_id, data.current_password, data.new_password)
    return {"success": success}


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset."""
    token = await service.reset_password_request(db, data.email)
    return {"token": token}

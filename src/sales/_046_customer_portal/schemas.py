"""
Schemas for Customer Portal.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any

from shared.types import BaseSchema


class PortalRegistration(BaseSchema):
    customer_code: str
    username: str
    email: str
    password: str


class PortalLogin(BaseSchema):
    username: str
    password: str


class PortalUserResponse(BaseSchema):
    id: int
    customer_code: str
    username: str
    email: str
    is_active: bool
    last_login: datetime | None
    created_at: datetime


class PortalDashboardData(BaseSchema):
    customer_code: str
    recent_orders: list[dict[str, Any]]
    outstanding_invoices: list[dict[str, Any]]
    total_spend: Decimal
    outstanding_amount: Decimal


class OrderHistoryResponse(BaseSchema):
    orders: list[dict[str, Any]]
    total_count: int


class ChangePasswordRequest(BaseSchema):
    current_password: str
    new_password: str


class ResetPasswordRequest(BaseSchema):
    email: str


class ResetPasswordResponse(BaseSchema):
    token: str

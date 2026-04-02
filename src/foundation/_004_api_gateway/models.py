"""
Database models for API Gateway configuration.
Provides models for routing and rate limiting.
"""
from typing import Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel


class GatewayRoute(BaseModel):
    """Configuration for an API Gateway route."""
    __tablename__ = "api_gateway_routes"

    path: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    target_url: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RateLimitRule(BaseModel):
    """Configuration for API Rate Limiting."""
    __tablename__ = "api_rate_limit_rules"

    path: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    client_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    max_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

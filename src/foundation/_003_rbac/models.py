from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.types import BaseModel


class Role(BaseModel):
    __tablename__ = "role"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Permission(BaseModel):
    __tablename__ = "permission"

    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    effect: Mapped[str] = mapped_column(String(20), nullable=False)


class RolePermission(BaseModel):
    __tablename__ = "role_permission"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uix_role_permission"),)

    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("role.id"), nullable=False)
    permission_id: Mapped[int] = mapped_column(Integer, ForeignKey("permission.id"), nullable=False)


class UserRole(BaseModel):
    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uix_user_role"),)

    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("role.id"), nullable=False)

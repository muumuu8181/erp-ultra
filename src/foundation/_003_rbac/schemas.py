from typing import Optional

from pydantic import Field

from shared.types import BaseSchema


class RoleCreate(BaseSchema):
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class RoleResponse(BaseSchema):
    id: int
    name: str
    description: Optional[str]
    is_active: bool


class PermissionCreate(BaseSchema):
    resource: str = Field(..., max_length=100)
    action: str = Field(..., max_length=100)
    effect: str = Field(..., max_length=20)


class PermissionResponse(BaseSchema):
    id: int
    resource: str
    action: str
    effect: str


class UserRoleCreate(BaseSchema):
    user_id: str = Field(..., max_length=100)
    role_id: int


class UserRoleResponse(BaseSchema):
    id: int
    user_id: str
    role_id: int

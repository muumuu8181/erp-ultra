from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database import get_db
from src.foundation._003_rbac import service
from src.foundation._003_rbac.schemas import (
    PermissionCreate,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    UserRoleCreate,
    UserRoleResponse,
)

router = APIRouter(prefix="/api/v1/rbac", tags=["rbac"])


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role_in: RoleCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_role(db, role_in)


@router.get("/roles", response_model=List[RoleResponse])
async def get_roles(db: AsyncSession = Depends(get_db)):
    return await service.get_roles(db)


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)):
    return await service.get_role(db, role_id)


@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(perm_in: PermissionCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_permission(db, perm_in)


@router.get("/permissions", response_model=List[PermissionResponse])
async def get_permissions(db: AsyncSession = Depends(get_db)):
    return await service.get_permissions(db)


@router.post("/roles/{role_id}/permissions/{permission_id}", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(role_id: int, permission_id: int, db: AsyncSession = Depends(get_db)):
    await service.assign_permission_to_role(db, role_id, permission_id)
    return {"message": "Permission assigned to role successfully"}


@router.post("/users/roles", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_user_role(user_role_in: UserRoleCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_user_role(db, user_role_in)


@router.get("/users/{user_id}/roles", response_model=List[RoleResponse])
async def get_user_roles(user_id: str, db: AsyncSession = Depends(get_db)):
    return await service.get_user_roles(db, user_id)


class PermissionCheckRequest(BaseModel):
    user_id: str
    resource: str
    action: str


class PermissionCheckResponse(BaseModel):
    allowed: bool


@router.post("/check_permission", response_model=PermissionCheckResponse)
async def check_permission(req: PermissionCheckRequest, db: AsyncSession = Depends(get_db)):
    allowed = await service.check_permission(db, req.user_id, req.resource, req.action)
    return {"allowed": allowed}

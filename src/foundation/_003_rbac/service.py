from typing import List

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError, ValidationError
from src.foundation._003_rbac.models import Permission, Role, RolePermission, UserRole
from src.foundation._003_rbac.schemas import PermissionCreate, RoleCreate, UserRoleCreate
from src.foundation._003_rbac.validators import validate_effect


async def create_role(db: AsyncSession, role_in: RoleCreate) -> Role:
    role = Role(**role_in.model_dump())
    db.add(role)
    try:
        await db.commit()
        await db.refresh(role)
        return role
    except IntegrityError:
        await db.rollback()
        raise ValidationError(f"Role with name '{role_in.name}' already exists.")


async def get_role(db: AsyncSession, role_id: int) -> Role:
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalars().first()
    if not role:
        raise NotFoundError(f"Role with ID {role_id} not found.")
    return role


async def get_roles(db: AsyncSession) -> List[Role]:
    result = await db.execute(select(Role))
    return list(result.scalars().all())


async def create_permission(db: AsyncSession, perm_in: PermissionCreate) -> Permission:
    validate_effect(perm_in.effect)
    perm = Permission(**perm_in.model_dump())
    db.add(perm)
    await db.commit()
    await db.refresh(perm)
    return perm


async def get_permissions(db: AsyncSession) -> List[Permission]:
    result = await db.execute(select(Permission))
    return list(result.scalars().all())


async def assign_permission_to_role(db: AsyncSession, role_id: int, permission_id: int) -> None:
    # Verify role exists
    await get_role(db, role_id)

    # Verify permission exists
    result = await db.execute(select(Permission).where(Permission.id == permission_id))
    if not result.scalars().first():
        raise NotFoundError(f"Permission with ID {permission_id} not found.")

    rp = RolePermission(role_id=role_id, permission_id=permission_id)
    db.add(rp)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        pass # Already assigned


async def create_user_role(db: AsyncSession, user_role_in: UserRoleCreate) -> UserRole:
    await get_role(db, user_role_in.role_id)
    user_role = UserRole(**user_role_in.model_dump())
    db.add(user_role)
    await db.commit()
    await db.refresh(user_role)
    return user_role


async def get_user_roles(db: AsyncSession, user_id: str) -> List[Role]:
    result = await db.execute(
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    return list(result.scalars().all())


async def check_permission(db: AsyncSession, user_id: str, resource: str, action: str) -> bool:
    """
    Checks if user_id is linked to an active role that has permission for resource/action with effect='allow'.
    """
    result = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            and_(
                UserRole.user_id == user_id,
                Role.is_active.is_(True),
                Permission.resource == resource,
                Permission.action == action,
                Permission.effect == "allow"
            )
        )
    )
    return result.scalars().first() is not None

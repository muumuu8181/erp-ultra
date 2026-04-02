import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError
from src.foundation._003_rbac import service
from src.foundation._003_rbac.schemas import PermissionCreate, RoleCreate, UserRoleCreate


@pytest.mark.asyncio
async def test_role_crud(db_session: AsyncSession):
    role_in = RoleCreate(name="editor", description="Editor role")
    role = await service.create_role(db_session, role_in)
    assert role.id is not None
    assert role.name == "editor"

    # duplicate role name test
    with pytest.raises(ValidationError):
        await service.create_role(db_session, role_in)

    roles = await service.get_roles(db_session)
    assert len(roles) > 0

@pytest.mark.asyncio
async def test_permission_crud(db_session: AsyncSession):
    perm_in = PermissionCreate(resource="posts", action="write", effect="allow")
    perm = await service.create_permission(db_session, perm_in)
    assert perm.id is not None
    assert perm.resource == "posts"

    perms = await service.get_permissions(db_session)
    assert len(perms) > 0

@pytest.mark.asyncio
async def test_check_permission(db_session: AsyncSession):
    # Setup
    role = await service.create_role(db_session, RoleCreate(name="author"))
    perm = await service.create_permission(
        db_session,
        PermissionCreate(resource="articles", action="publish", effect="allow")
    )

    await service.assign_permission_to_role(db_session, role.id, perm.id)

    user_id = "user_456"
    await service.create_user_role(db_session, UserRoleCreate(user_id=user_id, role_id=role.id))

    # Check
    has_perm = await service.check_permission(db_session, user_id, "articles", "publish")
    assert has_perm is True

    # Check non-existent perm
    has_perm_false = await service.check_permission(db_session, user_id, "articles", "delete")
    assert has_perm_false is False

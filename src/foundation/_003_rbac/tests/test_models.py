import pytest
from sqlalchemy import select

from src.foundation._003_rbac.models import Permission, Role, RolePermission, UserRole


@pytest.mark.asyncio
async def test_create_models(db_session):
    role = Role(name="admin", description="Admin role")
    db_session.add(role)
    await db_session.commit()

    perm = Permission(resource="users", action="create", effect="allow")
    db_session.add(perm)
    await db_session.commit()

    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    db_session.add(rp)

    ur = UserRole(user_id="user_123", role_id=role.id)
    db_session.add(ur)
    await db_session.commit()

    # Verify
    result_role = await db_session.execute(select(Role).where(Role.name == "admin"))
    assert result_role.scalars().first() is not None

    result_perm = await db_session.execute(select(Permission).where(Permission.resource == "users"))
    assert result_perm.scalars().first() is not None

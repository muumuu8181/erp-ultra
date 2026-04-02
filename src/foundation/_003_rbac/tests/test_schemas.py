import pytest
from pydantic import ValidationError

from src.foundation._003_rbac.schemas import PermissionCreate, RoleCreate


def test_role_create_valid():
    role = RoleCreate(name="admin", description="Admin role", is_active=True)
    assert role.name == "admin"
    assert role.description == "Admin role"
    assert role.is_active is True

def test_role_create_invalid():
    with pytest.raises(ValidationError):
        # name is required
        RoleCreate()

def test_permission_create_valid():
    perm = PermissionCreate(resource="users", action="read", effect="allow")
    assert perm.resource == "users"

def test_permission_create_invalid():
    with pytest.raises(ValidationError):
        PermissionCreate(resource="users") # missing action and effect

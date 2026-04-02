# 003_rbac

Role-Based Access Control module.

## Models
- `Role`: name, description, is_active
- `Permission`: resource, action, effect (allow/deny)
- `RolePermission`: Mapping between Role and Permission
- `UserRole`: Mapping between user_id and Role

## API Endpoints
- `POST /api/v1/rbac/roles`: Create a role
- `GET /api/v1/rbac/roles`: List roles
- `POST /api/v1/rbac/permissions`: Create a permission
- `POST /api/v1/rbac/roles/{role_id}/permissions/{permission_id}`: Map permission to role
- `POST /api/v1/rbac/users/roles`: Assign role to user
- `POST /api/v1/rbac/check_permission`: Check if a user has access to a resource/action

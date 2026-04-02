# 031 Audit Log Module

This module provides the Audit Log functionality for the ERP system, allowing tracking of user actions across entities.

## Features
- Create audit logs with user and entity tracking
- Retrieve individual audit logs or list all of them (paginated)
- Update/Delete audit logs (CRUD completeness)

## Example usage

```python
from src.domain._031_audit_log.schemas import AuditLogCreate
from src.domain._031_audit_log.service import create_audit_log

# Create a new audit log
new_log_data = AuditLogCreate(
    action="UPDATE",
    entity_name="User",
    entity_id="123",
    user_id="admin_1",
    details="Updated user email to admin@example.com"
)
audit_log = await create_audit_log(db_session, new_log_data)
```

# 031 Audit Log

The Audit Log module provides an append-only ledger for critical system actions.
It records who did what to which entity, along with the changes made in a structured format (JSON).

## Usage Example

### Create an Audit Log
```python
from src.domain._031_audit_log.schemas import AuditLogCreate
from src.domain._031_audit_log.service import create_audit_log

audit_data = AuditLogCreate(
    action="UPDATE",
    entity_name="User",
    entity_id="123",
    user_id="admin_1",
    changes={"email": {"old": "a@b.com", "new": "b@c.com"}}
)

new_log = await create_audit_log(db_session, audit_data)
```

### Retrieve Audit Logs
```python
from src.domain._031_audit_log.service import get_audit_logs

logs = await get_audit_logs(
    db_session,
    page=1,
    page_size=10,
    action="UPDATE",
    entity_name="User"
)
```

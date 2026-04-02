# Notification System (032)

Module for managing multi-channel notifications (in-app, email, Slack). Supports templated notifications with variable substitution, bulk sending, and read-status tracking.

## Usage

```python
# Create a notification template
data = NotificationTemplateCreate(
    code="WELCOME_EMAIL",
    name="Welcome Email",
    subject="Welcome {{name}}!",
    body_template="Hi {{name}}, thanks for joining.",
    channel=ChannelEnum.email,
    module="core"
)
template = await service.create_template(db, data)

# Send a notification using the template
notif_data = NotificationCreate(
    template_id=template.id,
    user_id="U123",
    channel=ChannelEnum.email,
    subject="",
    body="",
    template_vars={"name": "Alice"}
)
notif = await service.send_notification(db, notif_data)

# Mark as read
await service.mark_as_read(db, notif.id)
```

## Structure
- `models.py`: `NotificationTemplate`, `Notification`
- `schemas.py`: Request/Response schemas including `NotificationCreate`, `NotificationFilter`.
- `service.py`: Business logic (send_notification, send_bulk, get_stats, etc.)
- `router.py`: API routes mapped under `/api/v1/notifications`
- `validators.py`: Custom validations enforcing user_id, enum values, and template correctness.

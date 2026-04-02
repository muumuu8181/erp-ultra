# 030 Attachment Module

Provides attachment management for the Ultra ERP system.

## Usage

```python
from src.domain._030_attachment import AttachmentCreate, create_attachment

# Create a new attachment
attachment_data = AttachmentCreate(
    code="ATT-001",
    name="invoice.pdf",
)

# Call service
# attachment = await create_attachment(db, attachment_data)
```

# _007_queue

Async Message Queue module for ERP system.

## Usage

```python
from src.foundation._007_queue import enqueue, dequeue, complete_message

# Enqueue a message
await enqueue(db, "orders", QueueMessageCreate(payload='{"order_id": 1}'))

# Dequeue a message
messages = await dequeue(db, "orders")
if messages:
    msg = messages[0]
    # Process message
    await complete_message(db, msg.id)
```

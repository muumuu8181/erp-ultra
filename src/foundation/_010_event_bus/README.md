# Event Bus Module (`_010_event_bus`)

Provides inter-module event communication following the `EventBus` interface. This allows decoupled modules to react to each other's domain events asynchronously.

## Features

- **Decoupled Architecture**: Publish-subscribe pattern for inter-module communication.
- **Audit Trails**: All events are persisted as `EventRecord` with payload and status.
- **Error Isolation**: Individual handler failures do not prevent other handlers from processing an event.
- **Wildcard Subscriptions**: Allows listening to specific events (`module.action`), all events from a module (`module.*`), or all events globally (`*`).
- **Replay Capabilities**: Support for re-publishing past events.

## Usage

```python
from src.foundation._010_event_bus import DatabaseEventBus

bus = DatabaseEventBus(db_session)

# Subscribe to an event
async def my_handler(event):
    print(event.data)

await bus.subscribe("sales_order.created", my_handler)

# Publish an event
from shared.interfaces import Event
event = Event(event_type="sales_order.created", module="sales_order", data={"id": 1})
await bus.publish(event)
```

import pytest
import asyncio
from shared.errors import DuplicateError, NotFoundError
from src.foundation._010_event_bus.service import (
    publish_event, subscribe_handler, unsubscribe_handler,
    replay_event, get_event_history, get_subscriptions,
    _subscribers, DatabaseEventBus
)
from src.foundation._010_event_bus.schemas import EventFilter

@pytest.fixture(autouse=True)
def clear_subscribers():
    _subscribers.clear()

@pytest.mark.asyncio
async def test_publish_event_success(db_session):
    async def mock_handler(event):
        pass

    _subscribers["test.event"] = [mock_handler]

    record = await publish_event(db_session, "test.event", "test_module", {"foo": "bar"})
    assert record.status == "processed"
    assert record.processed_at is not None

@pytest.mark.asyncio
async def test_publish_event_error_isolation(db_session):
    handler1_called = False
    handler2_called = False

    async def failing_handler(event):
        nonlocal handler1_called
        handler1_called = True
        raise ValueError("Oops")

    async def succeeding_handler(event):
        nonlocal handler2_called
        handler2_called = True

    _subscribers["test.event"] = [failing_handler, succeeding_handler]

    record = await publish_event(db_session, "test.event", "test_module", {})

    assert handler1_called is True
    assert handler2_called is True
    assert record.status == "failed"
    assert "Oops" in record.error_message

@pytest.mark.asyncio
async def test_subscribe_handler(db_session):
    sub = await subscribe_handler(db_session, "test.event", "my_module", "my_func")
    assert sub.is_active is True

    # Duplicate should fail
    with pytest.raises(DuplicateError):
        await subscribe_handler(db_session, "test.event", "my_module", "my_func")

@pytest.mark.asyncio
async def test_unsubscribe_handler(db_session):
    sub = await subscribe_handler(db_session, "test.event", "my_module", "my_func")
    await unsubscribe_handler(db_session, sub.id)

    # Refresh logic not strictly needed, but let's check it deactivated
    subs = await get_subscriptions(db_session)
    assert len(subs) == 0

    with pytest.raises(NotFoundError):
        await unsubscribe_handler(db_session, 999)

@pytest.mark.asyncio
async def test_replay_event(db_session):
    record = await publish_event(db_session, "test.event", "test_module", {"foo": "bar"})

    replayed = await replay_event(db_session, record.id)
    assert replayed.id != record.id
    assert replayed.payload == record.payload

    with pytest.raises(NotFoundError):
        await replay_event(db_session, 999)

@pytest.mark.asyncio
async def test_get_event_history(db_session):
    await publish_event(db_session, "test.event1", "test_module1", {})
    await publish_event(db_session, "test.event2", "test_module2", {})

    filters = EventFilter(event_type="test.event1")
    items, total = await get_event_history(db_session, filters)
    assert total == 1
    assert items[0].event_type == "test.event1"

@pytest.mark.asyncio
async def test_wildcard_matching(db_session):
    called = []

    async def h_specific(e): called.append("specific")
    async def h_module(e): called.append("module")
    async def h_all(e): called.append("all")

    _subscribers["test.event"] = [h_specific]
    _subscribers["test.*"] = [h_module]
    _subscribers["*"] = [h_all]

    await publish_event(db_session, "test.event", "test", {})
    assert "specific" in called
    assert "module" in called
    assert "all" in called

@pytest.mark.asyncio
async def test_database_event_bus_interface(db_session):
    bus = DatabaseEventBus(db_session)

    async def handler(event):
        pass

    await bus.subscribe("test.event", handler)
    assert handler in _subscribers["test.event"]

    await bus.unsubscribe("test.event", handler)
    assert handler not in _subscribers["test.event"]

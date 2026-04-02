import pytest
from sqlalchemy.exc import IntegrityError
from src.foundation._010_event_bus.models import EventRecord, EventSubscription

@pytest.mark.asyncio
async def test_event_record_creation(db_session):
    record = EventRecord(
        event_type="test.created",
        source_module="test_module",
        payload={"key": "value"}
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)

    assert record.id is not None
    assert record.event_type == "test.created"
    assert record.source_module == "test_module"
    assert record.payload == {"key": "value"}
    assert record.status == "published"
    assert record.published_at is not None
    assert record.processed_at is None
    assert record.error_message is None
    assert repr(record).startswith("<EventRecord")

@pytest.mark.asyncio
async def test_event_subscription_creation(db_session):
    sub = EventSubscription(
        event_type="test.*",
        handler_module="test_handler",
        handler_function="handle_test"
    )
    db_session.add(sub)
    await db_session.commit()
    await db_session.refresh(sub)

    assert sub.id is not None
    assert sub.is_active is True
    assert "test_handler.handle_test" in repr(sub)

@pytest.mark.asyncio
async def test_event_subscription_unique_constraint(db_session):
    sub1 = EventSubscription(
        event_type="test.*",
        handler_module="test_handler",
        handler_function="handle_test"
    )
    db_session.add(sub1)
    await db_session.commit()

    sub2 = EventSubscription(
        event_type="test.*",
        handler_module="test_handler",
        handler_function="handle_test"
    )
    db_session.add(sub2)
    with pytest.raises(IntegrityError):
        await db_session.commit()

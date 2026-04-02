import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.errors import NotFoundError
from shared.types import Base
from src.foundation._007_queue.models import DeadLetterMessage, MessageStatus, QueueMessage
from src.foundation._007_queue.schemas import QueueMessageCreate
from src.foundation._007_queue.service import (
    clear_queue_state,
    complete_message,
    dequeue,
    enqueue,
    fail_message,
    get_or_create_queue,
    get_queue_stats,
    list_dead_letters,
    move_to_dead_letter,
    purge_queue,
    retry_failed,
)

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    clear_queue_state()

@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_enqueue_success(db: AsyncSession):
    msg = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    assert msg.id is not None
    assert msg.status == MessageStatus.PENDING

    q = get_or_create_queue("test_queue")
    assert not q.empty()

@pytest.mark.asyncio
async def test_enqueue_with_priority(db: AsyncSession):
    await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}', priority=10))
    await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 2}', priority=20))

    q = get_or_create_queue("test_queue")
    item1 = await q.get()
    assert item1[0] == -20

@pytest.mark.asyncio
async def test_enqueue_scheduled(db: AsyncSession):
    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}', scheduled_at=future))

    q = get_or_create_queue("test_queue")
    assert q.empty()

@pytest.mark.asyncio
async def test_dequeue_success(db: AsyncSession):
    await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    msgs = await dequeue(db, "test_queue")
    assert len(msgs) == 1
    assert msgs[0].status == MessageStatus.PROCESSING

@pytest.mark.asyncio
async def test_dequeue_empty_queue(db: AsyncSession):
    msgs = await dequeue(db, "test_queue")
    assert len(msgs) == 0

@pytest.mark.asyncio
async def test_dequeue_multiple(db: AsyncSession):
    await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 2}'))
    msgs = await dequeue(db, "test_queue", max_messages=2)
    assert len(msgs) == 2

@pytest.mark.asyncio
async def test_dequeue_priority_order(db: AsyncSession):
    msg1 = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}', priority=10))
    msg2 = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 2}', priority=20))
    msgs = await dequeue(db, "test_queue", max_messages=2)
    assert msgs[0].id == msg2.id
    assert msgs[1].id == msg1.id

@pytest.mark.asyncio
async def test_complete_message_success(db: AsyncSession):
    msg = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    await dequeue(db, "test_queue")
    completed = await complete_message(db, msg.id)
    assert completed.status == MessageStatus.COMPLETED

@pytest.mark.asyncio
async def test_complete_message_not_found(db: AsyncSession):
    with pytest.raises(NotFoundError):
        await complete_message(db, 999)

@pytest.mark.asyncio
async def test_fail_message_retry(db: AsyncSession):
    msg = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}', max_retries=3))
    await dequeue(db, "test_queue")
    failed = await fail_message(db, msg.id, "error")
    assert failed.status == MessageStatus.PENDING
    assert failed.retry_count == 1
    q = get_or_create_queue("test_queue")
    assert not q.empty()

@pytest.mark.asyncio
async def test_fail_message_exceeds_retries(db: AsyncSession):
    msg = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}', max_retries=1))
    await dequeue(db, "test_queue")
    failed = await fail_message(db, msg.id, "error")
    assert failed.status == MessageStatus.FAILED

@pytest.mark.asyncio
async def test_move_to_dead_letter(db: AsyncSession):
    msg = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    dlm = await move_to_dead_letter(db, msg.id, "fatal error")
    assert dlm.error_message == "fatal error"
    assert dlm.original_message_id == msg.id

    await db.refresh(msg)
    assert msg.status == MessageStatus.FAILED

@pytest.mark.asyncio
async def test_retry_failed(db: AsyncSession):
    msg = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    await move_to_dead_letter(db, msg.id, "err")
    retried = await retry_failed(db, "test_queue")
    assert len(retried) == 1
    assert retried[0].status == MessageStatus.PENDING

@pytest.mark.asyncio
async def test_get_queue_stats(db: AsyncSession):
    await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    stats = await get_queue_stats(db, "test_queue")
    assert stats.pending_count == 1
    assert stats.total_count == 1

@pytest.mark.asyncio
async def test_purge_queue(db: AsyncSession):
    await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    count = await purge_queue(db, "test_queue")
    assert count == 1
    q = get_or_create_queue("test_queue")
    assert q.empty()

@pytest.mark.asyncio
async def test_list_dead_letters(db: AsyncSession):
    msg = await enqueue(db, "test_queue", QueueMessageCreate(payload='{"a": 1}'))
    await move_to_dead_letter(db, msg.id, "err")
    res = await list_dead_letters(db, "test_queue")
    assert res.total == 1
    assert res.items[0].error_message == "err"

def test_clear_queue_state():
    get_or_create_queue("test_queue").put_nowait(1)
    clear_queue_state()
    q = get_or_create_queue("test_queue")
    assert q.empty()

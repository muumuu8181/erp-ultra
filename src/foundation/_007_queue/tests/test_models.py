from src.foundation._007_queue.models import DeadLetterMessage, MessageStatus, QueueMessage

def test_queue_message_creation():
    msg = QueueMessage(
        queue_name="test",
        payload="{}",
        status=MessageStatus.PENDING.value,
        priority=0,
        retry_count=0,
        max_retries=3
    )
    assert msg.queue_name == "test"
    assert msg.payload == "{}"
    assert msg.status == MessageStatus.PENDING.value
    assert msg.priority == 0
    assert msg.retry_count == 0
    assert msg.max_retries == 3

def test_dead_letter_message_creation():
    dlm = DeadLetterMessage(original_message_id=1, queue_name="test", payload="{}", error_message="error")
    assert dlm.original_message_id == 1
    assert dlm.queue_name == "test"
    assert dlm.payload == "{}"
    assert dlm.error_message == "error"

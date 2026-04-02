from src.foundation._006_logging.models import LogEntry

def test_log_entry_model_creation():
    entry = LogEntry(
        level="INFO",
        message="Test message",
        module="test_module",
        trace_id="12345",
        user_id="user1",
        metadata_={"key": "value"}
    )
    assert entry.level == "INFO"
    assert entry.message == "Test message"
    assert entry.module == "test_module"
    assert entry.trace_id == "12345"
    assert entry.user_id == "user1"
    assert entry.metadata_ == {"key": "value"}

import pytest
from shared.errors import ValidationError
from src.foundation._006_logging.schemas import LogEntryCreate
from src.foundation._006_logging.validators import validate_log_level, validate_log_entry_create

def test_validate_log_level_valid():
    validate_log_level("INFO")
    validate_log_level("debug")
    validate_log_level("ERROR")

def test_validate_log_level_invalid():
    with pytest.raises(ValidationError):
        validate_log_level("INVALID_LEVEL")

def test_validate_log_entry_create_valid():
    data = LogEntryCreate(level="INFO", message="Test", module="test_module")
    validate_log_entry_create(data)

def test_validate_log_entry_create_empty_message():
    data = LogEntryCreate(level="INFO", message="   ", module="test_module")
    with pytest.raises(ValidationError) as exc:
        validate_log_entry_create(data)
    assert exc.value.field == "message"

def test_validate_log_entry_create_empty_module():
    data = LogEntryCreate(level="INFO", message="Test", module="")
    with pytest.raises(ValidationError) as exc:
        validate_log_entry_create(data)
    assert exc.value.field == "module"

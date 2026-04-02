import pytest

from shared.errors import ValidationError
from src.foundation._007_queue.validators import (
    validate_json_payload,
    validate_max_retries,
    validate_priority,
    validate_queue_name,
)

def test_validate_queue_name_valid():
    validate_queue_name("orders")
    validate_queue_name("email_notifications")
    validate_queue_name("report-generation")

def test_validate_queue_name_too_short():
    with pytest.raises(ValidationError):
        validate_queue_name("a")

def test_validate_queue_name_uppercase():
    with pytest.raises(ValidationError):
        validate_queue_name("Orders")

def test_validate_queue_name_spaces():
    with pytest.raises(ValidationError):
        validate_queue_name("my queue")

def test_validate_json_payload_valid():
    validate_json_payload('{"key": "value"}')
    validate_json_payload('[]')

def test_validate_json_payload_invalid():
    with pytest.raises(ValidationError):
        validate_json_payload('invalid json')

def test_validate_max_retries_valid():
    validate_max_retries(0)
    validate_max_retries(1)
    validate_max_retries(3)
    validate_max_retries(10)

def test_validate_max_retries_negative():
    with pytest.raises(ValidationError):
        validate_max_retries(-1)

def test_validate_max_retries_too_large():
    with pytest.raises(ValidationError):
        validate_max_retries(11)

def test_validate_priority_valid():
    validate_priority(0)
    validate_priority(1)
    validate_priority(50)
    validate_priority(100)

def test_validate_priority_negative():
    with pytest.raises(ValidationError):
        validate_priority(-1)

def test_validate_priority_too_large():
    with pytest.raises(ValidationError):
        validate_priority(101)

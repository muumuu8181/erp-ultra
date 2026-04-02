from pydantic import ValidationError as PydanticValidationError
import pytest
from src.foundation._011_validators.schemas import ValidationRuleCreate, ValidationRequest

def test_validation_rule_create_schema_valid():
    data = {
        "name": "email_regex",
        "description": "Checks email",
        "rule_type": "regex",
        "parameters": {"pattern": ".*@.*"},
        "error_message": "Invalid email"
    }
    schema = ValidationRuleCreate(**data)
    assert schema.name == "email_regex"
    assert schema.is_active is True

def test_validation_rule_create_schema_invalid():
    with pytest.raises(PydanticValidationError):
        ValidationRuleCreate(
            name="a" * 51, # max_length 50
            rule_type="regex",
            error_message="Error"
        )

def test_validation_request_schema():
    req = ValidationRequest(rule_name="my_rule", value=123)
    assert req.rule_name == "my_rule"
    assert req.value == 123

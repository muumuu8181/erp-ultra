from datetime import datetime
from src.foundation._011_validators.models import ValidationRule

def test_validation_rule_model_init():
    rule = ValidationRule(
        name="test_rule",
        description="A test rule",
        rule_type="regex",
        parameters={"pattern": "^[0-9]+$"},
        error_message="Must be numbers only"
    )

    assert rule.name == "test_rule"
    assert rule.description == "A test rule"
    assert rule.rule_type == "regex"
    assert rule.parameters == {"pattern": "^[0-9]+$"}
    assert rule.error_message == "Must be numbers only"

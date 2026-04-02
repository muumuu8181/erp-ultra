import pytest

from shared.errors import ValidationError
from src.foundation._003_rbac.validators import validate_effect


def test_validate_effect_allow():
    validate_effect("allow")

def test_validate_effect_deny():
    validate_effect("deny")

def test_validate_effect_invalid():
    with pytest.raises(ValidationError):
        validate_effect("invalid")

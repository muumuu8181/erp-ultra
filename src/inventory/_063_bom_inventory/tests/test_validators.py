import pytest
from src.inventory._063_bom_inventory.validators import validate_positive_quantity
from shared.errors import ValidationError

def test_validate_positive_quantity_success():
    # Should not raise exception
    validate_positive_quantity(1)
    validate_positive_quantity(100)


def test_validate_positive_quantity_failure():
    with pytest.raises(ValidationError):
        validate_positive_quantity(0)

    with pytest.raises(ValidationError):
        validate_positive_quantity(-1)

# Cyclic dependency logic is already thoroughly tested in test_service.py through the service layer which hits the database.

"""
Validators for Sales Commission module.
"""
from decimal import Decimal
from shared.errors import ValidationError
from .schemas import CommissionCreate, CommissionUpdate

def validate_commission_rate(rate: Decimal) -> None:
    """Validates that commission rate is between 0 and 100."""
    if rate < 0 or rate > 100:
        raise ValidationError(
            message="Commission rate must be between 0 and 100",
            field="commission_rate"
        )

def validate_amount(amount: Decimal) -> None:
    """Validates that amount is non-negative."""
    if amount < 0:
        raise ValidationError(
            message="Amount cannot be negative",
            field="amount"
        )

def validate_commission_create(data: CommissionCreate) -> None:
    """Validates data for commission creation."""
    validate_commission_rate(data.commission_rate)
    validate_amount(data.amount)

def validate_commission_update(data: CommissionUpdate) -> None:
    """Validates data for commission update."""
    if data.commission_rate is not None:
        validate_commission_rate(data.commission_rate)
    if data.amount is not None:
        validate_amount(data.amount)

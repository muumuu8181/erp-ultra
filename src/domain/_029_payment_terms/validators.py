"""
Validators for Payment Terms module.
"""
from shared.errors import ValidationError
from src.domain._029_payment_terms.schemas import PaymentTermCreate, PaymentTermUpdate


def validate_payment_term_create(data: PaymentTermCreate) -> None:
    """
    Validate data when creating a Payment Term.
    """
    if not data.code or not data.code.strip():
        raise ValidationError("Code is required and cannot be empty", field="code")

    if not data.name or not data.name.strip():
        raise ValidationError("Name is required and cannot be empty", field="name")

    if data.days < 0:
        raise ValidationError("Days cannot be negative", field="days")


def validate_payment_term_update(data: PaymentTermUpdate) -> None:
    """
    Validate data when updating a Payment Term.
    """
    if data.code is not None and not data.code.strip():
        raise ValidationError("Code cannot be empty", field="code")

    if data.name is not None and not data.name.strip():
        raise ValidationError("Name cannot be empty", field="name")

    if data.days is not None and data.days < 0:
        raise ValidationError("Days cannot be negative", field="days")

import re

from shared.errors import ValidationError
from src.domain._016_customer_model.schemas import CustomerCreate, CustomerUpdate


def validate_customer_code(code: str) -> None:
    """Validate customer code format: must match CUS-XXXXX where X is alphanumeric."""
    if not code:
        raise ValidationError("Customer code cannot be empty.", field="code")
    if not re.match(r"^CUS-[A-Za-z0-9]{5}$", code):
        raise ValidationError("Invalid customer code format. Must be CUS-XXXXX where X is alphanumeric.", field="code")


def validate_email(email: str) -> None:
    """Validate email format using regex."""
    if not email:
        return
    email_regex = re.compile(
        r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    )
    if not email_regex.match(email):
        raise ValidationError("Invalid email format.", field="email")


def validate_phone(phone: str) -> None:
    """Validate Japanese phone number format."""
    if not phone:
        return
    # Accepts: 0X-XXXX-XXXX, 0XX-XXXX-XXXX, 0XXX-XX-XXXX
    phone_regex = re.compile(
        r"^(0\d-\d{4}-\d{4}|0\d{2}-\d{4}-\d{4}|0\d{3}-\d{2}-\d{4})$"
    )
    if not phone_regex.match(phone):
        raise ValidationError("Invalid Japanese phone number format.", field="phone")


def validate_corporate_number(number: str) -> None:
    """Validate Japanese corporate number (13 digits with check digit)."""
    if not number:
        return

    if len(number) != 13 or not number.isdigit():
        raise ValidationError("Corporate number must be 13 digits.", field="corporate_number")

    digits = [int(d) for d in number]
    first_12 = digits[:12]
    total_sum = 0
    for i, d in enumerate(first_12):
        weight = 1 if i % 2 == 0 else 2
        total_sum += d * weight

    check_digit = (9 - (total_sum % 9)) % 9

    if check_digit != digits[12]:
        raise ValidationError("Invalid corporate number check digit.", field="corporate_number")


def validate_customer_create(data: CustomerCreate) -> None:
    """Run all validations for customer creation."""
    validate_customer_code(data.code)
    if data.email:
        validate_email(data.email)
    if data.phone:
        validate_phone(data.phone)
    if data.corporate_number:
        validate_corporate_number(data.corporate_number)


def validate_customer_update(data: CustomerUpdate) -> None:
    """Run all validations for customer update (only for non-None fields)."""
    if data.email is not None:
        validate_email(data.email)
    if data.phone is not None:
        validate_phone(data.phone)
    if data.corporate_number is not None:
        validate_corporate_number(data.corporate_number)

import re
from typing import Optional

from shared.errors import ValidationError

def validate_phone_number(phone: Optional[str]) -> None:
    """
    Validates a phone number using a simple regex pattern.
    Accepts digits, +, -, (, ), and spaces.
    Raises ValidationError if invalid.
    """
    if not phone:
        return

    # Pattern allows +, digits, spaces, parentheses, hyphens. Needs to have at least a digit.
    pattern = r'^[+\d\s()-]+$'
    if not re.match(pattern, phone) or not any(c.isdigit() for c in phone):
        raise ValidationError("Invalid phone number format.")

def validate_contact_relations(customer_id: Optional[int], supplier_id: Optional[int]) -> None:
    """
    Validates that a contact is associated with either a customer or a supplier, or neither,
    but maybe log or raise if we want strict rules. For now, just ensure it's not logically flawed
    (though a contact could be both if the business logic allows, often they are separate).
    """
    # For now, no strict exclusivity, but placeholder for business logic if needed.
    pass

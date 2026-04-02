"""
Validators for the _036_quotation module.
"""
from datetime import date
from typing import List, Optional
from decimal import Decimal

from shared.errors import ValidationError, BusinessRuleError
from shared.types import DocumentStatus
from src.sales._036_quotation.schemas import QuotationCreate, QuotationUpdate, QuotationLineCreate


def validate_valid_until_date(quotation_date: date, valid_until: date) -> None:
    """1. valid_until >= quotation_date"""
    if valid_until < quotation_date:
        raise ValidationError("valid_until must be on or after quotation_date", field="valid_until")


def validate_lines_not_empty(lines: List[QuotationLineCreate]) -> None:
    """2. At least one line"""
    if not lines:
        raise ValidationError("quotation must have at least one line item", field="lines")


def validate_positive_quantities(lines: List[QuotationLineCreate]) -> None:
    """3. Positive quantities"""
    for idx, line in enumerate(lines):
        if line.quantity <= 0:
            raise ValidationError(f"quantity must be greater than 0 for line {line.line_number}", field=f"lines[{idx}].quantity")


def validate_sequential_line_numbers(lines: List[QuotationLineCreate]) -> None:
    """4. Sequential line numbers"""
    sorted_lines = sorted(lines, key=lambda x: x.line_number)
    for i, line in enumerate(sorted_lines, start=1):
        if line.line_number != i:
            raise ValidationError("line_number must be sequential starting from 1", field="lines")


def validate_customer_code(customer_code: str) -> None:
    """5. customer_code not empty"""
    if not customer_code or not customer_code.strip():
        raise ValidationError("customer_code must be a non-empty string", field="customer_code")


def validate_unit_price(lines: List[QuotationLineCreate]) -> None:
    """7. Unit price non-negative"""
    for idx, line in enumerate(lines):
        if line.unit_price < 0:
            raise ValidationError(f"unit_price must be non-negative for line {line.line_number}", field=f"lines[{idx}].unit_price")


def validate_discount_percentage(lines: List[QuotationLineCreate]) -> None:
    """8. Discount range"""
    for idx, line in enumerate(lines):
        if not (Decimal('0') <= line.discount_percentage <= Decimal('100')):
            raise ValidationError(f"discount_percentage must be between 0 and 100 for line {line.line_number}", field=f"lines[{idx}].discount_percentage")


def validate_quotation_creation(data: QuotationCreate) -> None:
    validate_customer_code(data.customer_code)
    validate_valid_until_date(data.quotation_date, data.valid_until)
    validate_lines_not_empty(data.lines)
    validate_positive_quantities(data.lines)
    validate_sequential_line_numbers(data.lines)
    validate_unit_price(data.lines)
    validate_discount_percentage(data.lines)


def validate_quotation_update(current_data: dict, update_data: QuotationUpdate) -> None:
    quotation_date = update_data.quotation_date or current_data.get('quotation_date')
    valid_until = update_data.valid_until or current_data.get('valid_until')

    if quotation_date and valid_until:
        validate_valid_until_date(quotation_date, valid_until)

    if update_data.customer_code is not None:
        validate_customer_code(update_data.customer_code)

    if update_data.lines is not None:
        validate_lines_not_empty(update_data.lines)
        validate_positive_quantities(update_data.lines)
        validate_sequential_line_numbers(update_data.lines)
        validate_unit_price(update_data.lines)
        validate_discount_percentage(update_data.lines)


def validate_status_transition(current_status: DocumentStatus, new_status: DocumentStatus) -> None:
    """6. Status transitions"""
    valid_transitions = {
        DocumentStatus.DRAFT: [DocumentStatus.PENDING_APPROVAL, DocumentStatus.CANCELLED, DocumentStatus.VOID],
        DocumentStatus.PENDING_APPROVAL: [DocumentStatus.APPROVED, DocumentStatus.REJECTED, DocumentStatus.CANCELLED, DocumentStatus.VOID],
        DocumentStatus.APPROVED: [DocumentStatus.CANCELLED, DocumentStatus.VOID],
        DocumentStatus.REJECTED: [DocumentStatus.CANCELLED, DocumentStatus.VOID],
        DocumentStatus.CANCELLED: [],
        DocumentStatus.VOID: []
    }

    if new_status not in valid_transitions.get(current_status, []):
        raise BusinessRuleError(f"Cannot transition status from {current_status} to {new_status}")

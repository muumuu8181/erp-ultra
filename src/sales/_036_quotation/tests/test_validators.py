"""
Tests for _036_quotation validators.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from shared.errors import ValidationError, BusinessRuleError
from shared.types import DocumentStatus, TaxType
from src.sales._036_quotation.schemas import QuotationLineCreate, QuotationCreate
from src.sales._036_quotation.validators import (
    validate_valid_until_date,
    validate_lines_not_empty,
    validate_positive_quantities,
    validate_sequential_line_numbers,
    validate_customer_code,
    validate_unit_price,
    validate_discount_percentage,
    validate_status_transition
)


def test_valid_until_date():
    validate_valid_until_date(date.today(), date.today())
    with pytest.raises(ValidationError):
        validate_valid_until_date(date.today(), date.today() - timedelta(days=1))


def test_lines_not_empty():
    with pytest.raises(ValidationError):
        validate_lines_not_empty([])


def test_positive_quantities():
    with pytest.raises(ValueError):
        QuotationLineCreate(
            line_number=1, product_code="P1", product_name="P1", quantity=Decimal('-1'), unit_price=Decimal('10'), tax_type=TaxType.STANDARD_10
        )


def test_sequential_line_numbers():
    lines = [
        QuotationLineCreate(line_number=1, product_code="P1", product_name="P1", quantity=Decimal('1'), unit_price=Decimal('10'), tax_type=TaxType.STANDARD_10),
        QuotationLineCreate(line_number=3, product_code="P2", product_name="P2", quantity=Decimal('1'), unit_price=Decimal('10'), tax_type=TaxType.STANDARD_10)
    ]
    with pytest.raises(ValidationError):
        validate_sequential_line_numbers(lines)


def test_customer_code():
    with pytest.raises(ValidationError):
        validate_customer_code("")


def test_unit_price():
    with pytest.raises(ValueError):
        QuotationLineCreate(line_number=1, product_code="P1", product_name="P1", quantity=Decimal('1'), unit_price=Decimal('-10'), tax_type=TaxType.STANDARD_10)


def test_discount_percentage():
    with pytest.raises(ValueError):
        QuotationLineCreate(line_number=1, product_code="P1", product_name="P1", quantity=Decimal('1'), unit_price=Decimal('10'), discount_percentage=Decimal('101'), tax_type=TaxType.STANDARD_10)


def test_status_transitions():
    validate_status_transition(DocumentStatus.DRAFT, DocumentStatus.PENDING_APPROVAL)
    with pytest.raises(BusinessRuleError):
        validate_status_transition(DocumentStatus.DRAFT, DocumentStatus.APPROVED)

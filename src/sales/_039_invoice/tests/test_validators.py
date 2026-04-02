import pytest
from datetime import date
from decimal import Decimal
from shared.errors import ValidationError, BusinessRuleError
from shared.types import TaxType
from src.sales._039_invoice.schemas import InvoiceCreate, InvoiceLineCreate, InvoicePaymentCreate
from src.sales._039_invoice.models import Invoice, InvoiceStatus
from src.sales._039_invoice.validators import validate_invoice_create, validate_invoice_payment, validate_invoice_cancellation

def test_validate_invoice_create_valid():
    data = InvoiceCreate(
        customer_code="CUST01",
        customer_name="Test",
        invoice_date=date(2023, 10, 1),
        due_date=date(2023, 10, 31),
        lines=[
            InvoiceLineCreate(
                product_code="P1",
                product_name="Prod1",
                quantity=Decimal('1'),
                unit_price=Decimal('100'),
                tax_type=TaxType.STANDARD_10
            )
        ]
    )
    validate_invoice_create(data)

def test_validate_invoice_create_invalid_due_date():
    data = InvoiceCreate(
        customer_code="CUST01",
        customer_name="Test",
        invoice_date=date(2023, 10, 31),
        due_date=date(2023, 10, 1),
        lines=[
            InvoiceLineCreate(
                product_code="P1",
                product_name="Prod1",
                quantity=Decimal('1'),
                unit_price=Decimal('100'),
                tax_type=TaxType.STANDARD_10
            )
        ]
    )
    with pytest.raises(ValidationError, match="due_date must be on or after invoice_date"):
        validate_invoice_create(data)

def test_validate_invoice_create_no_lines():
    data = InvoiceCreate(
        customer_code="CUST01",
        customer_name="Test",
        invoice_date=date(2023, 10, 1),
        due_date=date(2023, 10, 31),
        lines=[]
    )
    with pytest.raises(ValidationError, match="invoice must have at least one line item"):
        validate_invoice_create(data)

def test_validate_invoice_payment_exceeds_balance():
    invoice = Invoice(total_amount=Decimal('100'), paid_amount=Decimal('50'), status=InvoiceStatus.DRAFT)
    payment = InvoicePaymentCreate(payment_date=date.today(), amount=Decimal('60'), payment_method="cash")
    with pytest.raises(ValidationError, match="payment amount cannot exceed remaining balance"):
        validate_invoice_payment(invoice, payment)

def test_validate_invoice_payment_cancelled():
    invoice = Invoice(total_amount=Decimal('100'), paid_amount=Decimal('0'), status=InvoiceStatus.CANCELLED)
    payment = InvoicePaymentCreate(payment_date=date.today(), amount=Decimal('50'), payment_method="cash")
    with pytest.raises(BusinessRuleError, match="cannot record payment on an invoice with cancelled status"):
        validate_invoice_payment(invoice, payment)

def test_validate_invoice_cancellation():
    invoice = Invoice(paid_amount=Decimal('50'))
    with pytest.raises(BusinessRuleError, match="cannot cancel if paid_amount > 0"):
        validate_invoice_cancellation(invoice)

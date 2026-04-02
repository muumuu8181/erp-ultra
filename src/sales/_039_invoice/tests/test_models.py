import pytest
from datetime import date
from decimal import Decimal
from shared.types import TaxType
from src.sales._039_invoice.models import Invoice, InvoiceLine, InvoicePayment, InvoiceStatus

@pytest.mark.asyncio
async def test_invoice_model_creation():
    invoice = Invoice(
        invoice_number="INV-202310-0001",
        customer_code="CUST01",
        customer_name="Test Customer",
        invoice_date=date(2023, 10, 1),
        due_date=date(2023, 10, 31),
        status=InvoiceStatus.DRAFT,
        currency_code="USD",
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("10.00"),
        total_amount=Decimal("110.00"),
        paid_amount=Decimal("0.00"),
    )
    assert invoice.invoice_number == "INV-202310-0001"
    assert invoice.subtotal == Decimal("100.00")
    assert invoice.status == InvoiceStatus.DRAFT

@pytest.mark.asyncio
async def test_invoice_line_model():
    line = InvoiceLine(
        invoice_id=1,
        line_number=1,
        product_code="PROD01",
        product_name="Test Product",
        quantity=Decimal("2.0"),
        unit_price=Decimal("50.00"),
        tax_type=TaxType.STANDARD_10,
        line_amount=Decimal("100.00"),
    )
    assert line.line_number == 1
    assert line.tax_type == TaxType.STANDARD_10

@pytest.mark.asyncio
async def test_invoice_payment_model():
    payment = InvoicePayment(
        invoice_id=1,
        payment_date=date(2023, 10, 5),
        amount=Decimal("110.00"),
        payment_method="bank_transfer",
        reference="REF123"
    )
    assert payment.amount == Decimal("110.00")
    assert payment.payment_method == "bank_transfer"

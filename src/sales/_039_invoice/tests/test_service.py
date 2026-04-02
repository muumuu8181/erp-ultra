import pytest
from datetime import date
from decimal import Decimal
from shared.types import TaxType
from src.sales._039_invoice.models import Invoice, InvoiceLine
from src.sales._039_invoice.service import _calculate_totals

def test_calculate_totals():
    invoice = Invoice()
    invoice.lines = [
        InvoiceLine(
            quantity=Decimal('2'),
            unit_price=Decimal('100'),
            discount_percentage=Decimal('0'),
            tax_type=TaxType.STANDARD_10
        ),
        InvoiceLine(
            quantity=Decimal('1'),
            unit_price=Decimal('50'),
            discount_percentage=Decimal('10'),
            tax_type=TaxType.REDUCED_8
        )
    ]

    _calculate_totals(invoice)

    # Line 1: 2 * 100 = 200, Tax = 20
    # Line 2: 1 * 50 * 0.9 = 45, Tax = 3.6
    assert invoice.subtotal == Decimal('245.00')
    assert invoice.tax_amount == Decimal('23.60')
    assert invoice.total_amount == Decimal('268.60')

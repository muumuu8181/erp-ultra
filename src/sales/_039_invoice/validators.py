from decimal import Decimal
from shared.errors import ValidationError, BusinessRuleError
from .schemas import InvoiceCreate, InvoicePaymentCreate
from .models import Invoice, InvoiceStatus

def validate_invoice_create(data: InvoiceCreate) -> None:
    # 1. due_date >= invoice_date
    if data.due_date < data.invoice_date:
        raise ValidationError("due_date must be on or after invoice_date", field="due_date")

    # 2. At least one line
    if not data.lines:
        raise ValidationError("invoice must have at least one line item", field="lines")

    # 6. customer_code not empty
    if not data.customer_code.strip():
        raise ValidationError("customer_code must be a non-empty string", field="customer_code")

    for i, line in enumerate(data.lines, start=1):
        # 7. Positive quantities
        if line.quantity <= 0:
            raise ValidationError("quantity must be > 0 for every line", field=f"lines[{i-1}].quantity")
        # 8. Unit price non-negative
        if line.unit_price < 0:
            raise ValidationError("unit_price must be >= 0", field=f"lines[{i-1}].unit_price")
        # 9. Discount range
        if not (Decimal('0') <= line.discount_percentage <= Decimal('100')):
            raise ValidationError("discount_percentage must be between 0 and 100", field=f"lines[{i-1}].discount_percentage")


def validate_invoice_payment(invoice: Invoice, payment: InvoicePaymentCreate) -> None:
    # 4. Cannot pay cancelled invoice
    if invoice.status == InvoiceStatus.CANCELLED:
        raise BusinessRuleError("cannot record payment on an invoice with cancelled status")

    # 5. Positive payment amount
    if payment.amount <= 0:
        raise ValidationError("payment amount must be > 0", field="amount")

    # 3. payment_amount <= balance
    balance = invoice.total_amount - invoice.paid_amount
    if payment.amount > balance:
        raise ValidationError("payment amount cannot exceed remaining balance", field="amount")

def validate_invoice_cancellation(invoice: Invoice) -> None:
    # 11. Cannot cancel paid invoice
    if invoice.paid_amount > 0:
        raise BusinessRuleError("cannot cancel if paid_amount > 0")

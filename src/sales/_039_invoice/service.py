from datetime import date
from decimal import Decimal
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, func
from sqlalchemy.orm import selectinload

from shared.types import CodeGenerator, PaginatedResponse
from shared.errors import NotFoundError, DuplicateError, BusinessRuleError

from .models import Invoice, InvoiceLine, InvoicePayment, InvoiceStatus
from .schemas import InvoiceCreate, InvoiceUpdate, InvoiceListFilter, InvoicePaymentCreate, InvoiceResponse
from .validators import validate_invoice_create, validate_invoice_payment, validate_invoice_cancellation

async def calculate_balance(invoice: Invoice) -> Decimal:
    """Calculate the remaining balance of an invoice."""
    return invoice.total_amount - invoice.paid_amount

def _calculate_totals(invoice: Invoice) -> None:
    """Recalculate subtotal, tax, and total amount for an invoice based on lines."""
    subtotal = Decimal('0')
    tax_amount = Decimal('0')

    for line in invoice.lines:
        discount_factor = Decimal('1') - (line.discount_percentage / Decimal('100'))
        line.line_amount = line.quantity * line.unit_price * discount_factor

        tax_rate = Decimal('0')
        if line.tax_type == "standard_10":
            tax_rate = Decimal('0.10')
        elif line.tax_type == "reduced_8":
            tax_rate = Decimal('0.08')

        tax_amount += line.line_amount * tax_rate
        subtotal += line.line_amount

    invoice.subtotal = subtotal
    invoice.tax_amount = tax_amount
    invoice.total_amount = subtotal + tax_amount

async def create_invoice(db: AsyncSession, data: InvoiceCreate) -> Invoice:
    """Create a new invoice."""
    validate_invoice_create(data)

    invoice_number = CodeGenerator.generate("INV")

    invoice = Invoice(
        invoice_number=invoice_number,
        order_number=data.order_number,
        customer_code=data.customer_code,
        customer_name=data.customer_name,
        invoice_date=data.invoice_date,
        due_date=data.due_date,
        currency_code=data.currency_code,
        payment_terms_code=data.payment_terms_code,
        billing_address=data.billing_address,
        notes=data.notes,
        status=InvoiceStatus.DRAFT,
        paid_amount=Decimal('0')
    )

    invoice.lines = []
    for idx, line_data in enumerate(data.lines, start=1):
        line = InvoiceLine(
            line_number=idx,
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            discount_percentage=line_data.discount_percentage,
            tax_type=line_data.tax_type,
        )
        invoice.lines.append(line)

    _calculate_totals(invoice)

    try:
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
    except exc.IntegrityError:
        await db.rollback()
        raise DuplicateError("Invoice", key=invoice_number)

    return invoice

async def get_invoice(db: AsyncSession, invoice_id: int) -> Invoice:
    """Retrieve an invoice by ID."""
    stmt = select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_id)
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Invoice", str(invoice_id))
    return invoice

async def update_invoice(db: AsyncSession, invoice_id: int, data: InvoiceUpdate) -> Invoice:
    """Update a draft invoice."""
    invoice = await get_invoice(db, invoice_id)
    if invoice.status != InvoiceStatus.DRAFT:
        raise BusinessRuleError("Only draft invoices can be updated.")

    if data.order_number is not None:
        invoice.order_number = data.order_number
    if data.customer_code is not None:
        invoice.customer_code = data.customer_code
    if data.customer_name is not None:
        invoice.customer_name = data.customer_name
    if data.invoice_date is not None:
        invoice.invoice_date = data.invoice_date
    if data.due_date is not None:
        invoice.due_date = data.due_date
    if data.currency_code is not None:
        invoice.currency_code = data.currency_code
    if data.payment_terms_code is not None:
        invoice.payment_terms_code = data.payment_terms_code
    if data.billing_address is not None:
        invoice.billing_address = data.billing_address
    if data.notes is not None:
        invoice.notes = data.notes

    if data.lines is not None:
        invoice.lines.clear()
        for idx, line_data in enumerate(data.lines, start=1):
            line = InvoiceLine(
                line_number=idx,
                product_code=line_data.product_code,
                product_name=line_data.product_name,
                description=line_data.description,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percentage=line_data.discount_percentage,
                tax_type=line_data.tax_type,
            )
            invoice.lines.append(line)
        _calculate_totals(invoice)

    if invoice.due_date < invoice.invoice_date:
        raise BusinessRuleError("due_date must be on or after invoice_date")

    await db.commit()
    await db.refresh(invoice)
    return invoice

async def list_invoices(db: AsyncSession, filters: InvoiceListFilter) -> PaginatedResponse[InvoiceResponse]:
    """List invoices with filters."""
    stmt = select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments))

    if filters.status:
        stmt = stmt.where(Invoice.status == filters.status)
    if filters.customer_code:
        stmt = stmt.where(Invoice.customer_code == filters.customer_code)
    if filters.date_from:
        stmt = stmt.where(Invoice.invoice_date >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(Invoice.invoice_date <= filters.date_to)
    if filters.overdue_only:
        stmt = stmt.where(Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]))
        stmt = stmt.where(Invoice.due_date < date.today())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return PaginatedResponse(
        items=[InvoiceResponse.model_validate(item) for item in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=math.ceil(total / filters.page_size) if filters.page_size else 1
    )

async def send_invoice(db: AsyncSession, invoice_id: int) -> Invoice:
    """Send an invoice, transitioning draft -> sent."""
    invoice = await get_invoice(db, invoice_id)
    if invoice.status != InvoiceStatus.DRAFT:
        raise BusinessRuleError("Only draft invoices can be sent.")

    invoice.status = InvoiceStatus.SENT
    await db.commit()
    await db.refresh(invoice)
    return invoice

async def record_payment(db: AsyncSession, invoice_id: int, data: InvoicePaymentCreate) -> Invoice:
    """Record a payment against an invoice."""
    invoice = await get_invoice(db, invoice_id)
    validate_invoice_payment(invoice, data)

    payment = InvoicePayment(
        payment_date=data.payment_date,
        amount=data.amount,
        payment_method=data.payment_method,
        reference=data.reference
    )
    invoice.payments.append(payment)

    invoice.paid_amount += payment.amount
    balance = await calculate_balance(invoice)

    if balance == 0:
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIALLY_PAID

    await db.commit()
    await db.refresh(invoice)
    return invoice

async def mark_overdue(db: AsyncSession) -> list[Invoice]:
    """Find and mark overdue invoices."""
    today = date.today()
    stmt = select(Invoice).where(
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID])
    ).where(Invoice.due_date < today)

    result = await db.execute(stmt)
    invoices = list(result.scalars().all())

    for inv in invoices:
        inv.status = InvoiceStatus.OVERDUE

    if invoices:
        await db.commit()
        for inv in invoices:
            await db.refresh(inv)

    return invoices

async def get_aging_report(db: AsyncSession, as_of_date: date) -> dict:
    """Get aging report for unpaid invoices."""
    stmt = select(Invoice).where(
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE])
    )
    result = await db.execute(stmt)
    invoices = list(result.scalars().all())

    report = {
        "0-30": Decimal('0'),
        "31-60": Decimal('0'),
        "61-90": Decimal('0'),
        "91+": Decimal('0')
    }

    for inv in invoices:
        days_overdue = (as_of_date - inv.due_date).days
        balance = inv.total_amount - inv.paid_amount
        if balance <= 0:
            continue

        if days_overdue <= 30:
            report["0-30"] += balance
        elif days_overdue <= 60:
            report["31-60"] += balance
        elif days_overdue <= 90:
            report["61-90"] += balance
        else:
            report["91+"] += balance

    return report

async def cancel_invoice(db: AsyncSession, invoice_id: int) -> Invoice:
    """Cancel an invoice."""
    invoice = await get_invoice(db, invoice_id)
    validate_invoice_cancellation(invoice)

    invoice.status = InvoiceStatus.CANCELLED
    await db.commit()
    await db.refresh(invoice)
    return invoice

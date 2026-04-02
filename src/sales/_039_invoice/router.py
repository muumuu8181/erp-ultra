from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from shared.types import PaginatedResponse

from . import service
from .models import InvoiceStatus
from .schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListFilter,
    InvoicePaymentCreate,
    PaginatedInvoiceResponse,
)

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

@router.post("/", response_model=InvoiceResponse, status_code=201)
async def create_invoice(data: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new invoice."""
    return await service.create_invoice(db, data)

@router.get("/", response_model=PaginatedInvoiceResponse)
async def list_invoices(
    status: InvoiceStatus | None = None,
    customer_code: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    overdue_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List invoices with filtering."""
    filters = InvoiceListFilter(
        status=status,
        customer_code=customer_code,
        date_from=date_from,
        date_to=date_to,
        overdue_only=overdue_only,
        page=page,
        page_size=page_size,
    )
    return await service.list_invoices(db, filters)

@router.get("/aging", response_model=dict[str, float])
async def get_aging_report(
    as_of_date: date | None = None, db: AsyncSession = Depends(get_db)
):
    """Get aging report for invoices."""
    if not as_of_date:
        as_of_date = date.today()
    return await service.get_aging_report(db, as_of_date)

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Get an invoice by ID."""
    return await service.get_invoice(db, invoice_id)

@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int, data: InvoiceUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an existing invoice."""
    return await service.update_invoice(db, invoice_id, data)

@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Transition a draft invoice to sent status."""
    return await service.send_invoice(db, invoice_id)

@router.post("/{invoice_id}/payments", response_model=InvoiceResponse)
async def record_payment(
    invoice_id: int, data: InvoicePaymentCreate, db: AsyncSession = Depends(get_db)
):
    """Record a payment against an invoice."""
    return await service.record_payment(db, invoice_id, data)

@router.post("/mark-overdue", response_model=list[InvoiceResponse])
async def mark_overdue(db: AsyncSession = Depends(get_db)):
    """Mark all eligible past-due invoices as overdue."""
    return await service.mark_overdue(db)

@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel an invoice."""
    return await service.cancel_invoice(db, invoice_id)

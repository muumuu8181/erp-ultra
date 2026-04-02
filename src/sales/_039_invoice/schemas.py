from datetime import date
from decimal import Decimal
from typing import Optional, List
from shared.types import BaseSchema, PaginatedResponse, TaxType
from .models import InvoiceStatus

class InvoiceLineCreate(BaseSchema):
    product_code: str
    product_name: str
    description: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal = Decimal('0.0')
    tax_type: TaxType

class InvoiceLineResponse(InvoiceLineCreate):
    id: int
    invoice_id: int
    line_number: int
    line_amount: Decimal

class InvoiceCreate(BaseSchema):
    order_number: Optional[str] = None
    customer_code: str
    customer_name: str
    invoice_date: date
    due_date: date
    currency_code: str = "USD"
    payment_terms_code: Optional[str] = None
    billing_address: Optional[str] = None
    notes: Optional[str] = None
    lines: List[InvoiceLineCreate]

class InvoiceUpdate(BaseSchema):
    order_number: Optional[str] = None
    customer_code: Optional[str] = None
    customer_name: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency_code: Optional[str] = None
    payment_terms_code: Optional[str] = None
    billing_address: Optional[str] = None
    notes: Optional[str] = None
    lines: Optional[List[InvoiceLineCreate]] = None

class InvoicePaymentCreate(BaseSchema):
    payment_date: date
    amount: Decimal
    payment_method: str
    reference: Optional[str] = None

class InvoicePaymentResponse(InvoicePaymentCreate):
    id: int
    invoice_id: int

class InvoiceResponse(BaseSchema):
    id: int
    invoice_number: str
    order_number: Optional[str]
    customer_code: str
    customer_name: str
    invoice_date: date
    due_date: date
    status: InvoiceStatus
    currency_code: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    payment_terms_code: Optional[str]
    billing_address: Optional[str]
    notes: Optional[str]
    created_by: Optional[str]

    lines: List[InvoiceLineResponse]
    payments: List[InvoicePaymentResponse]

    class Config:
        from_attributes = True

class PaginatedInvoiceResponse(PaginatedResponse[InvoiceResponse]):
    model_config = {"arbitrary_types_allowed": True}
    pass

class InvoiceListFilter(BaseSchema):
    status: Optional[InvoiceStatus] = None
    customer_code: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    overdue_only: Optional[bool] = False
    page: int = 1
    page_size: int = 50

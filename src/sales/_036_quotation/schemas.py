"""
Schemas for the _036_quotation module.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import Field

from shared.types import BaseSchema, DocumentStatus, TaxType, PaginatedResponse


class QuotationLineCreate(BaseSchema):
    line_number: int
    product_code: str
    product_name: str
    description: Optional[str] = None
    quantity: Decimal = Field(gt=0)
    unit: str = "PCS"
    unit_price: Decimal = Field(ge=0)
    discount_percentage: Decimal = Field(ge=0, le=100, default=Decimal('0'))
    tax_type: TaxType


class QuotationCreate(BaseSchema):
    customer_code: str
    customer_name: str
    quotation_date: date
    valid_until: date
    currency_code: str = "USD"
    notes: Optional[str] = None
    sales_person: Optional[str] = None
    lines: List[QuotationLineCreate]


class QuotationUpdate(BaseSchema):
    customer_code: Optional[str] = None
    customer_name: Optional[str] = None
    quotation_date: Optional[date] = None
    valid_until: Optional[date] = None
    currency_code: Optional[str] = None
    notes: Optional[str] = None
    sales_person: Optional[str] = None
    lines: Optional[List[QuotationLineCreate]] = None


class QuotationLineResponse(BaseSchema):
    id: int
    quotation_id: int
    line_number: int
    product_code: str
    product_name: str
    description: Optional[str] = None
    quantity: Decimal
    unit: str
    unit_price: Decimal
    discount_percentage: Decimal
    tax_type: TaxType
    line_amount: Decimal


class QuotationResponse(BaseSchema):
    id: int
    quotation_number: str
    customer_code: str
    customer_name: str
    quotation_date: date
    valid_until: date
    status: DocumentStatus
    currency_code: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: Optional[str] = None
    sales_person: Optional[str] = None
    created_by: Optional[str] = None
    lines: List[QuotationLineResponse]


class QuotationListFilter(BaseSchema):
    status: Optional[DocumentStatus] = None
    customer_code: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_expired: Optional[bool] = None
    page: int = 1
    page_size: int = 50

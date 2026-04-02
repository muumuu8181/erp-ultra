"""
Tests for _036_quotation models.
"""
import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.types import DocumentStatus, TaxType
from src.sales._036_quotation.models import Quotation, QuotationLine


@pytest.mark.asyncio
async def test_quotation_model_creation(db_session: AsyncSession):
    quotation = Quotation(
        quotation_number="QUO-202401-0001",
        customer_code="CUST-001",
        customer_name="Test Customer",
        quotation_date=date.today(),
        valid_until=date.today(),
        status=DocumentStatus.DRAFT,
        subtotal=100.0,
        tax_amount=10.0,
        total_amount=110.0
    )
    db_session.add(quotation)
    await db_session.commit()

    result = await db_session.execute(select(Quotation).where(Quotation.quotation_number == "QUO-202401-0001"))
    db_quotation = result.scalar_one()

    assert db_quotation.id is not None
    assert db_quotation.customer_code == "CUST-001"
    assert db_quotation.status == DocumentStatus.DRAFT


@pytest.mark.asyncio
async def test_quotation_line_creation_and_cascade(db_session: AsyncSession):
    quotation = Quotation(
        quotation_number="QUO-202401-0002",
        customer_code="CUST-002",
        customer_name="Test Customer 2",
        quotation_date=date.today(),
        valid_until=date.today()
    )
    db_session.add(quotation)
    await db_session.flush()

    line = QuotationLine(
        quotation_id=quotation.id,
        line_number=1,
        product_code="PROD-001",
        product_name="Test Product",
        quantity=10.0,
        unit="PCS",
        unit_price=10.0,
        tax_type=TaxType.STANDARD_10,
        line_amount=100.0
    )
    db_session.add(line)
    await db_session.commit()

    # Test cascade delete
    await db_session.delete(quotation)
    await db_session.commit()

    result = await db_session.execute(select(QuotationLine).where(QuotationLine.quotation_id == quotation.id))
    lines = result.scalars().all()
    assert len(lines) == 0

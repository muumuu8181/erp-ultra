"""
Tests for _036_quotation service.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from shared.types import DocumentStatus, TaxType
from shared.errors import DuplicateError, BusinessRuleError
from src.sales._036_quotation.schemas import QuotationCreate, QuotationLineCreate, QuotationUpdate, QuotationListFilter
from src.sales._036_quotation.service import (
    create_quotation,
    update_quotation,
    get_quotation,
    list_quotations,
    send_quotation,
    approve_quotation,
    reject_quotation,
    expire_quotation,
    convert_to_order,
    calculate_totals
)


@pytest.fixture
def valid_quotation_create() -> QuotationCreate:
    return QuotationCreate(
        customer_code="CUST-001",
        customer_name="Test Customer",
        quotation_date=date.today(),
        valid_until=date.today() + timedelta(days=30),
        lines=[
            QuotationLineCreate(
                line_number=1,
                product_code="PROD-001",
                product_name="Test Product 1",
                quantity=Decimal('10.0'),
                unit_price=Decimal('100.0'),
                tax_type=TaxType.STANDARD_10
            )
        ]
    )


@pytest.mark.asyncio
async def test_calculate_totals():
    lines = [
        QuotationLineCreate(line_number=1, product_code="P1", product_name="P1", quantity=Decimal('2'), unit_price=Decimal('100'), tax_type=TaxType.STANDARD_10),
        QuotationLineCreate(line_number=2, product_code="P2", product_name="P2", quantity=Decimal('1'), unit_price=Decimal('100'), discount_percentage=Decimal('10'), tax_type=TaxType.REDUCED_8)
    ]
    subtotal, tax, total = await calculate_totals(lines)
    assert subtotal == Decimal('290') # 200 + 90
    assert tax == Decimal('27.2') # 200*0.1 + 90*0.08
    assert total == Decimal('317.2')


@pytest.mark.asyncio
async def test_create_quotation(db_session: AsyncSession, valid_quotation_create: QuotationCreate):
    quotation = await create_quotation(db_session, valid_quotation_create)
    assert quotation.id is not None
    assert quotation.status == DocumentStatus.DRAFT
    assert len(quotation.lines) == 1
    assert quotation.subtotal == 1000.0


@pytest.mark.asyncio
async def test_duplicate_quotation_number(db_session: AsyncSession, valid_quotation_create: QuotationCreate):
    await create_quotation(db_session, valid_quotation_create)
    # create_quotation auto generates number based on date. To trigger integrity error,
    # we need to simulate the generation logic outputting the same number, or just modify the record manually.
    # We will manually create a second quotation with the exact same number to test the integrity error.
    from src.sales._036_quotation.models import Quotation
    dup = Quotation(
        quotation_number="QUO-202604-0001",
        customer_code="test",
        customer_name="test",
        quotation_date=date.today(),
        valid_until=date.today() + timedelta(days=1),
        status=DocumentStatus.DRAFT,
        subtotal=0,
        tax_amount=0,
        total_amount=0
    )
    db_session.add(dup)

    # Test through the service layer catching it
    with pytest.raises(DuplicateError):
        from shared.types import CodeGenerator
        prefix_key = f"QUO-{date.today().strftime('%Y%m')}"
        CodeGenerator._counters[prefix_key] -= 1 # reset to get same number
        await create_quotation(db_session, valid_quotation_create)


@pytest.mark.asyncio
async def test_update_quotation_only_draft(db_session: AsyncSession, valid_quotation_create: QuotationCreate):
    quotation = await create_quotation(db_session, valid_quotation_create)
    await send_quotation(db_session, quotation.id)

    update_data = QuotationUpdate(notes="Updated")
    with pytest.raises(BusinessRuleError):
        await update_quotation(db_session, quotation.id, update_data)


@pytest.mark.asyncio
async def test_status_transitions(db_session: AsyncSession, valid_quotation_create: QuotationCreate):
    quotation = await create_quotation(db_session, valid_quotation_create)

    # send
    q_sent = await send_quotation(db_session, quotation.id)
    assert q_sent.status == DocumentStatus.PENDING_APPROVAL

    # approve
    q_app = await approve_quotation(db_session, quotation.id)
    assert q_app.status == DocumentStatus.APPROVED

@pytest.mark.asyncio
async def test_reject_quotation(db_session: AsyncSession, valid_quotation_create: QuotationCreate):
    quotation = await create_quotation(db_session, valid_quotation_create)
    await send_quotation(db_session, quotation.id)

    q_rej = await reject_quotation(db_session, quotation.id)
    assert q_rej.status == DocumentStatus.REJECTED

@pytest.mark.asyncio
async def test_expire_quotation(db_session: AsyncSession, valid_quotation_create: QuotationCreate):
    # Make valid_until in the past
    valid_quotation_create.valid_until = date.today() - timedelta(days=1)

    # Needs to bypass Pydantic validation that valid_until >= quotation_date
    # But wait, create_quotation will fail if valid_until < quotation_date.
    # So we need to make both quotation_date and valid_until in the past.
    valid_quotation_create.quotation_date = date.today() - timedelta(days=2)

    quotation = await create_quotation(db_session, valid_quotation_create)

    q_exp = await expire_quotation(db_session, quotation.id)
    assert q_exp.status == DocumentStatus.VOID


@pytest.mark.asyncio
async def test_convert_to_order(db_session: AsyncSession, valid_quotation_create: QuotationCreate):
    quotation = await create_quotation(db_session, valid_quotation_create)
    await send_quotation(db_session, quotation.id)
    await approve_quotation(db_session, quotation.id)

    order_data = await convert_to_order(db_session, quotation.id)
    assert order_data["customer_code"] == "CUST-001"
    assert len(order_data["lines"]) == 1


@pytest.mark.asyncio
async def test_list_quotations(db_session: AsyncSession, valid_quotation_create: QuotationCreate):
    await create_quotation(db_session, valid_quotation_create)
    filters = QuotationListFilter(status=DocumentStatus.DRAFT)
    response = await list_quotations(db_session, filters)
    assert response.total >= 1
    assert len(response.items) >= 1

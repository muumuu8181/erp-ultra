"""
Service for the _036_quotation module.
"""
from datetime import date
from decimal import Decimal
from typing import Tuple, List, Dict, Any

from sqlalchemy import select, exc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.types import DocumentStatus, CodeGenerator, PaginatedResponse, TaxType
from shared.errors import NotFoundError, DuplicateError, BusinessRuleError
from src.sales._036_quotation.models import Quotation, QuotationLine
from src.sales._036_quotation.schemas import QuotationCreate, QuotationUpdate, QuotationListFilter, QuotationLineCreate, QuotationResponse
from src.sales._036_quotation.validators import validate_quotation_creation, validate_quotation_update, validate_status_transition


async def calculate_totals(lines: List[QuotationLineCreate]) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate subtotal, tax amount, and total amount for a list of quotation lines.

    Args:
        lines: List of QuotationLineCreate schemas representing the lines of the quotation.

    Returns:
        A tuple containing (subtotal, tax_amount, total_amount) as Decimals.
    """
    subtotal = Decimal('0')
    tax_amount = Decimal('0')

    for line in lines:
        discounted_price = line.unit_price * (1 - (line.discount_percentage / Decimal('100')))
        line_amount = line.quantity * discounted_price
        subtotal += line_amount

        # Calculate tax based on TaxType
        if line.tax_type == TaxType.STANDARD_10:
            tax_rate = Decimal('0.10')
        elif line.tax_type == TaxType.REDUCED_8:
            tax_rate = Decimal('0.08')
        elif line.tax_type == TaxType.EXEMPT or line.tax_type == TaxType.NON_TAXABLE:
            tax_rate = Decimal('0')
        else:
            tax_rate = Decimal('0')

        tax_amount += line_amount * tax_rate

    # Round logic can be adapted based on company rules, using basic quantize here
    total_amount = subtotal + tax_amount
    return subtotal, tax_amount, total_amount


async def create_quotation(db: AsyncSession, data: QuotationCreate) -> Quotation:
    """
    Create a new quotation.

    Args:
        db: The async database session.
        data: The QuotationCreate schema containing quotation data.

    Returns:
        The newly created Quotation instance.

    Raises:
        DuplicateError: If a quotation with the generated number already exists.
        ValidationError: If input data is invalid.
    """
    validate_quotation_creation(data)

    quotation_number = CodeGenerator.generate("QUO", data.quotation_date)

    subtotal, tax_amount, total_amount = await calculate_totals(data.lines)

    new_quotation = Quotation(
        quotation_number=quotation_number,
        customer_code=data.customer_code,
        customer_name=data.customer_name,
        quotation_date=data.quotation_date,
        valid_until=data.valid_until,
        currency_code=data.currency_code,
        notes=data.notes,
        sales_person=data.sales_person,
        status=DocumentStatus.DRAFT,
        subtotal=float(subtotal),
        tax_amount=float(tax_amount),
        total_amount=float(total_amount),
    )

    db.add(new_quotation)
    try:
        await db.flush()
    except exc.IntegrityError:
        await db.rollback()
        raise DuplicateError("Quotation", "quotation_number")

    for line_data in data.lines:
        discounted_price = line_data.unit_price * (1 - (line_data.discount_percentage / Decimal('100')))
        line_amount = line_data.quantity * discounted_price

        line = QuotationLine(
            quotation_id=new_quotation.id,
            line_number=line_data.line_number,
            product_code=line_data.product_code,
            product_name=line_data.product_name,
            description=line_data.description,
            quantity=float(line_data.quantity),
            unit=line_data.unit,
            unit_price=float(line_data.unit_price),
            discount_percentage=float(line_data.discount_percentage),
            tax_type=line_data.tax_type,
            line_amount=float(line_amount)
        )
        db.add(line)

    await db.commit()
    await db.refresh(new_quotation, ["lines"])
    return new_quotation


async def get_quotation(db: AsyncSession, quotation_id: int) -> Quotation:
    """
    Retrieve a quotation by its ID.

    Args:
        db: The async database session.
        quotation_id: The ID of the quotation to retrieve.

    Returns:
        The retrieved Quotation instance including its lines.

    Raises:
        NotFoundError: If the quotation with the given ID does not exist.
    """
    result = await db.execute(select(Quotation).options(selectinload(Quotation.lines)).where(Quotation.id == quotation_id))
    quotation = result.scalar_one_or_none()
    if not quotation:
        raise NotFoundError("Quotation", str(quotation_id))
    return quotation


async def update_quotation(db: AsyncSession, quotation_id: int, data: QuotationUpdate) -> Quotation:
    """
    Update an existing quotation. Only allowed in DRAFT status.

    Args:
        db: The async database session.
        quotation_id: The ID of the quotation to update.
        data: The QuotationUpdate schema containing fields to update.

    Returns:
        The updated Quotation instance.

    Raises:
        BusinessRuleError: If the quotation is not in DRAFT status.
        NotFoundError: If the quotation does not exist.
        ValidationError: If the updated data is invalid.
    """
    quotation = await get_quotation(db, quotation_id)

    if quotation.status != DocumentStatus.DRAFT:
        raise BusinessRuleError("Only draft quotations can be updated")

    current_data = {
        "quotation_date": quotation.quotation_date,
        "valid_until": quotation.valid_until
    }
    validate_quotation_update(current_data, data)

    update_dict = data.model_dump(exclude_unset=True)
    lines_data = update_dict.pop("lines", None)

    for key, value in update_dict.items():
        setattr(quotation, key, value)

    if lines_data is not None:
        # Re-calculate totals if lines are updated
        lines_create_objs = [QuotationLineCreate(**ld) for ld in lines_data]
        subtotal, tax_amount, total_amount = await calculate_totals(lines_create_objs)
        quotation.subtotal = float(subtotal)
        quotation.tax_amount = float(tax_amount)
        quotation.total_amount = float(total_amount)

        # Replace lines completely
        for existing_line in quotation.lines:
            await db.delete(existing_line)

        quotation.lines = []
        await db.flush()

        for line_data in lines_create_objs:
            discounted_price = line_data.unit_price * (1 - (line_data.discount_percentage / Decimal('100')))
            line_amount = line_data.quantity * discounted_price

            new_line = QuotationLine(
                quotation_id=quotation.id,
                line_number=line_data.line_number,
                product_code=line_data.product_code,
                product_name=line_data.product_name,
                description=line_data.description,
                quantity=float(line_data.quantity),
                unit=line_data.unit,
                unit_price=float(line_data.unit_price),
                discount_percentage=float(line_data.discount_percentage),
                tax_type=line_data.tax_type,
                line_amount=float(line_amount)
            )
            db.add(new_line)

    await db.commit()
    await db.refresh(quotation, ["lines"])
    return quotation


async def list_quotations(db: AsyncSession, filters: QuotationListFilter) -> PaginatedResponse[QuotationResponse]:
    """
    List quotations based on provided filters, with pagination.

    Args:
        db: The async database session.
        filters: The QuotationListFilter schema containing filter parameters.

    Returns:
        A PaginatedResponse containing a list of QuotationResponse objects.
    """
    query = select(Quotation).options(selectinload(Quotation.lines))

    if filters.status:
        query = query.where(Quotation.status == filters.status)
    if filters.customer_code:
        query = query.where(Quotation.customer_code == filters.customer_code)
    if filters.date_from:
        query = query.where(Quotation.quotation_date >= filters.date_from)
    if filters.date_to:
        query = query.where(Quotation.quotation_date <= filters.date_to)
    if filters.is_expired is not None:
        if filters.is_expired:
            query = query.where(Quotation.valid_until < date.today())
        else:
            query = query.where(Quotation.valid_until >= date.today())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Pagination
    offset = (filters.page - 1) * filters.page_size
    query = query.offset(offset).limit(filters.page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = (total + filters.page_size - 1) // filters.page_size

    items_response = [QuotationResponse.model_validate(i) for i in items]

    return PaginatedResponse(
        items=items_response,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages
    )


async def send_quotation(db: AsyncSession, quotation_id: int) -> Quotation:
    """
    Transition a quotation's status to PENDING_APPROVAL.

    Args:
        db: The async database session.
        quotation_id: The ID of the quotation.

    Returns:
        The updated Quotation instance.

    Raises:
        BusinessRuleError: If the transition is invalid.
    """
    quotation = await get_quotation(db, quotation_id)
    validate_status_transition(quotation.status, DocumentStatus.PENDING_APPROVAL)
    quotation.status = DocumentStatus.PENDING_APPROVAL
    await db.commit()
    await db.refresh(quotation, ["lines"])
    return quotation


async def approve_quotation(db: AsyncSession, quotation_id: int) -> Quotation:
    """
    Transition a quotation's status to APPROVED.

    Args:
        db: The async database session.
        quotation_id: The ID of the quotation.

    Returns:
        The updated Quotation instance.

    Raises:
        BusinessRuleError: If the transition is invalid.
    """
    quotation = await get_quotation(db, quotation_id)
    validate_status_transition(quotation.status, DocumentStatus.APPROVED)
    quotation.status = DocumentStatus.APPROVED
    await db.commit()
    await db.refresh(quotation, ["lines"])
    return quotation


async def reject_quotation(db: AsyncSession, quotation_id: int) -> Quotation:
    """
    Transition a quotation's status to REJECTED.

    Args:
        db: The async database session.
        quotation_id: The ID of the quotation.

    Returns:
        The updated Quotation instance.

    Raises:
        BusinessRuleError: If the transition is invalid.
    """
    quotation = await get_quotation(db, quotation_id)
    validate_status_transition(quotation.status, DocumentStatus.REJECTED)
    quotation.status = DocumentStatus.REJECTED
    await db.commit()
    await db.refresh(quotation, ["lines"])
    return quotation


async def expire_quotation(db: AsyncSession, quotation_id: int) -> Quotation:
    """
    Transition a quotation's status to VOID (expired).
    Only valid if the valid_until date is in the past.

    Args:
        db: The async database session.
        quotation_id: The ID of the quotation.

    Returns:
        The updated Quotation instance.

    Raises:
        BusinessRuleError: If the valid_until date is not in the past or transition is invalid.
    """
    quotation = await get_quotation(db, quotation_id)
    if quotation.valid_until >= date.today():
        raise BusinessRuleError("Cannot expire quotation before valid_until date")

    validate_status_transition(quotation.status, DocumentStatus.VOID)
    quotation.status = DocumentStatus.VOID
    await db.commit()
    await db.refresh(quotation, ["lines"])
    return quotation


async def convert_to_order(db: AsyncSession, quotation_id: int) -> dict:
    """
    Convert an approved quotation into a sales order data structure.
    Does not create the sales order directly.

    Args:
        db: The async database session.
        quotation_id: The ID of the quotation to convert.

    Returns:
        A dictionary containing the sales order data.

    Raises:
        BusinessRuleError: If the quotation is not in APPROVED status.
    """
    quotation = await get_quotation(db, quotation_id)
    if quotation.status != DocumentStatus.APPROVED:
        raise BusinessRuleError("Only approved quotations can be converted to orders")

    order_data = {
        "customer_code": quotation.customer_code,
        "customer_name": quotation.customer_name,
        "order_date": date.today().isoformat(),
        "currency_code": quotation.currency_code,
        "notes": f"Converted from Quotation {quotation.quotation_number}. {quotation.notes or ''}".strip(),
        "sales_person": quotation.sales_person,
        "lines": []
    }

    for line in quotation.lines:
        order_data["lines"].append({
            "line_number": line.line_number,
            "product_code": line.product_code,
            "product_name": line.product_name,
            "description": line.description,
            "quantity": line.quantity,
            "unit": line.unit,
            "unit_price": line.unit_price,
            "discount_percentage": line.discount_percentage,
            "tax_type": line.tax_type.value,
        })

    return order_data

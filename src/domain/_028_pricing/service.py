from typing import Optional
from datetime import date
from decimal import Decimal

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain._028_pricing.models import PriceList, PriceListItem
from src.domain._028_pricing.schemas import (
    PriceListCreate, PriceListItemCreate, PriceLookupRequest, PriceLookupResponse
)
from src.domain._028_pricing.validators import (
    validate_date_range, validate_positive_price, validate_discount_percentage, validate_product_code_exists
)
from shared.types import PaginatedResponse
from shared.errors import NotFoundError, ValidationError, DuplicateError

async def create_price_list(db: AsyncSession, data: PriceListCreate) -> PriceList:
    """Create a new price list."""
    validate_date_range(data.valid_from, data.valid_to)

    result = await db.execute(select(PriceList).where(PriceList.code == data.code))
    if result.scalars().first():
        raise DuplicateError("Price list", data.code)

    price_list = PriceList(**data.model_dump())
    db.add(price_list)
    await db.commit()
    await db.refresh(price_list)
    return price_list


async def update_price_list(db: AsyncSession, price_list_id: int, data: PriceListCreate) -> PriceList:
    """Update an existing price list."""
    validate_date_range(data.valid_from, data.valid_to)

    result = await db.execute(select(PriceList).where(PriceList.id == price_list_id))
    price_list = result.scalars().first()
    if not price_list:
        raise NotFoundError("Price list", str(price_list_id))

    if data.code != price_list.code:
        check = await db.execute(select(PriceList).where(PriceList.code == data.code))
        if check.scalars().first():
            raise DuplicateError("Price list code", data.code)

    for key, value in data.model_dump().items():
        setattr(price_list, key, value)

    await db.commit()
    await db.refresh(price_list)
    return price_list


async def add_price_item(db: AsyncSession, price_list_id: int, data: PriceListItemCreate) -> PriceListItem:
    """Add a price item to a price list."""
    validate_positive_price(data.unit_price)
    validate_discount_percentage(data.discount_percentage)
    await validate_product_code_exists(db, data.product_code)

    result = await db.execute(select(PriceList).where(PriceList.id == price_list_id))
    if not result.scalars().first():
        raise NotFoundError("Price list", str(price_list_id))

    item = PriceListItem(price_list_id=price_list_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_price(db: AsyncSession, request: PriceLookupRequest) -> PriceLookupResponse:
    """Get the applicable price for a product."""
    target_date = request.date or date.today()

    query = select(PriceListItem, PriceList).join(PriceList).where(
        PriceList.is_active == True,
        PriceList.valid_from <= target_date,
        or_(PriceList.valid_to >= target_date, PriceList.valid_to.is_(None)),
        PriceListItem.product_code == request.product_code,
        PriceListItem.min_quantity <= request.quantity
    )

    if request.price_list_id is not None:
        query = query.where(PriceList.id == request.price_list_id)

    # Order by min_quantity desc to get the most specific tier first
    query = query.order_by(PriceListItem.min_quantity.desc())

    result = await db.execute(query)
    match = result.first()

    if not match:
        raise NotFoundError("Applicable price not found")

    item, price_list = match

    effective_price = item.unit_price * (Decimal('1') - item.discount_percentage / Decimal('100'))
    total_price = effective_price * request.quantity

    return PriceLookupResponse(
        product_code=item.product_code,
        price_list_id=price_list.id,
        price_list_code=price_list.code,
        unit_price=item.unit_price,
        discount_percentage=item.discount_percentage,
        effective_price=effective_price,
        min_quantity=item.min_quantity,
        quantity=request.quantity,
        total_price=total_price,
        currency_code=price_list.currency_code
    )


async def get_best_price(db: AsyncSession, request: PriceLookupRequest) -> PriceLookupResponse:
    """Get the best (lowest) price across all active price lists."""
    target_date = request.date or date.today()

    query = select(PriceListItem, PriceList).join(PriceList).where(
        PriceList.is_active == True,
        PriceList.valid_from <= target_date,
        or_(PriceList.valid_to >= target_date, PriceList.valid_to.is_(None)),
        PriceListItem.product_code == request.product_code,
        PriceListItem.min_quantity <= request.quantity
    )

    result = await db.execute(query)
    matches = result.all()

    if not matches:
        raise NotFoundError("Applicable price not found in any list")

    best_price_resp = None
    best_price = Decimal('Infinity')

    list_to_best_item = {}
    for item, price_list in matches:
        if price_list.id not in list_to_best_item:
            list_to_best_item[price_list.id] = (item, price_list)
        else:
            existing_item = list_to_best_item[price_list.id][0]
            if item.min_quantity > existing_item.min_quantity:
                list_to_best_item[price_list.id] = (item, price_list)

    for item, price_list in list_to_best_item.values():
        effective_price = item.unit_price * (Decimal('1') - item.discount_percentage / Decimal('100'))
        if effective_price < best_price:
            best_price = effective_price
            best_price_resp = PriceLookupResponse(
                product_code=item.product_code,
                price_list_id=price_list.id,
                price_list_code=price_list.code,
                unit_price=item.unit_price,
                discount_percentage=item.discount_percentage,
                effective_price=effective_price,
                min_quantity=item.min_quantity,
                quantity=request.quantity,
                total_price=effective_price * request.quantity,
                currency_code=price_list.currency_code
            )

    return best_price_resp


async def calculate_price(
    db: AsyncSession, product_code: str, quantity: Decimal, date_val: Optional[date] = None, price_list_id: Optional[int] = None
) -> PriceLookupResponse:
    """Calculate the final price for a product given quantity and optional date/list."""
    req = PriceLookupRequest(
        product_code=product_code,
        quantity=quantity,
        date=date_val,
        price_list_id=price_list_id
    )
    return await get_price(db, req)


async def list_price_lists(
    db: AsyncSession, is_active: Optional[bool] = None, page: int = 1, page_size: int = 50
) -> PaginatedResponse:
    """List price lists with optional filtering."""
    query = select(PriceList)
    if is_active is not None:
        query = query.where(PriceList.is_active == is_active)

    total_count = await db.scalar(select(func.count()).select_from(query.subquery()))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = (total_count + page_size - 1) // page_size if total_count else 0

    return PaginatedResponse(
        items=[item for item in items],
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


async def duplicate_price_list(db: AsyncSession, source_id: int, new_code: str, new_name: Optional[str] = None) -> PriceList:
    """Duplicate a price list with all its items."""
    source_list_result = await db.execute(select(PriceList).where(PriceList.id == source_id))
    source_list = source_list_result.scalars().first()

    if not source_list:
        raise NotFoundError("Price list", str(source_id))

    code_check = await db.execute(select(PriceList).where(PriceList.code == new_code))
    if code_check.scalars().first():
        raise DuplicateError("Price list code", new_code)

    new_list_name = new_name if new_name else f"Copy of {source_list.name}"

    new_list = PriceList(
        name=new_list_name,
        code=new_code,
        valid_from=source_list.valid_from,
        valid_to=source_list.valid_to,
        currency_code=source_list.currency_code,
        is_active=False
    )

    db.add(new_list)
    await db.flush()

    items_result = await db.execute(select(PriceListItem).where(PriceListItem.price_list_id == source_id))
    items = items_result.scalars().all()

    for item in items:
        new_item = PriceListItem(
            price_list_id=new_list.id,
            product_code=item.product_code,
            unit_price=item.unit_price,
            discount_percentage=item.discount_percentage,
            min_quantity=item.min_quantity
        )
        db.add(new_item)

    await db.commit()
    await db.refresh(new_list)
    return new_list

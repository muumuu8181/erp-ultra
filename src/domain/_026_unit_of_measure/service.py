"""
Unit of Measure service layer.
"""
import math
from typing import Optional
from collections import deque
from decimal import Decimal

from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain._026_unit_of_measure.models import UnitOfMeasure, UomConversion
from src.domain._026_unit_of_measure.schemas import (
    UomCreate, UomResponse, UomConversionCreate, UomConversionResponse,
    UomConvertRequest, UomConvertResponse
)
from src.domain._026_unit_of_measure.validators import (
    validate_code_unique, validate_factor_positive, validate_no_self_reference
)
from shared.types import PaginatedResponse
from shared.errors import NotFoundError, ValidationError, DuplicateError, BusinessRuleError


async def create_uom(db: AsyncSession, data: UomCreate) -> UnitOfMeasure:
    """Create a new unit of measure.

    Args:
        db: Database session.
        data: UOM creation data.
    Returns:
        The created UnitOfMeasure record.
    Raises:
        DuplicateError: If a UOM with the same code already exists.
    """
    code = validate_code_unique(data.code)

    # Check for existing code
    existing = await db.execute(select(UnitOfMeasure).where(UnitOfMeasure.code == code))
    if existing.scalar_one_or_none():
        raise DuplicateError("UnitOfMeasure", code)

    uom = UnitOfMeasure(
        code=code,
        name=data.name,
        symbol=data.symbol,
        uom_type=data.uom_type.value,
        decimal_places=data.decimal_places,
        is_active=data.is_active
    )
    db.add(uom)
    try:
        await db.commit()
        await db.refresh(uom)
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("UnitOfMeasure", code)

    return uom


async def list_uoms(
    db: AsyncSession, uom_type: Optional[str] = None, is_active: Optional[bool] = None,
    page: int = 1, page_size: int = 50
) -> PaginatedResponse[UomResponse]:
    """List units of measure with optional filtering.

    Args:
        db: Database session.
        uom_type: Optional filter by type.
        is_active: Optional filter by active status.
        page: Page number.
        page_size: Items per page.
    Returns:
        PaginatedResponse containing UomResponse items.
    """
    query = select(UnitOfMeasure)

    if uom_type is not None:
        query = query.where(UnitOfMeasure.uom_type == uom_type)
    if is_active is not None:
        query = query.where(UnitOfMeasure.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    query = query.order_by(UnitOfMeasure.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[UomResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )


async def create_conversion(db: AsyncSession, data: UomConversionCreate) -> UomConversion:
    """Create a conversion factor between two units.

    Args:
        db: Database session.
        data: Conversion creation data.
    Returns:
        The created UomConversion record.
    Raises:
        ValidationError: If factor <= 0 or self-referencing.
        NotFoundError: If from_uom_id or to_uom_id does not exist.
        DuplicateError: If conversion already exists.
    """
    await validate_no_self_reference(data.from_uom_id, data.to_uom_id)
    factor = validate_factor_positive(data.factor)

    # Check if UOMs exist
    from_uom_res = await db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == data.from_uom_id))
    from_uom = from_uom_res.scalar_one_or_none()
    if not from_uom:
        raise NotFoundError("UnitOfMeasure", str(data.from_uom_id))

    to_uom_res = await db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == data.to_uom_id))
    to_uom = to_uom_res.scalar_one_or_none()
    if not to_uom:
        raise NotFoundError("UnitOfMeasure", str(data.to_uom_id))

    # Check for existing conversion
    existing = await db.execute(
        select(UomConversion).where(
            UomConversion.from_uom_id == data.from_uom_id,
            UomConversion.to_uom_id == data.to_uom_id
        )
    )
    if existing.scalar_one_or_none():
        raise DuplicateError("UomConversion")

    conversion = UomConversion(
        from_uom_id=data.from_uom_id,
        to_uom_id=data.to_uom_id,
        factor=factor,
        is_standard=data.is_standard
    )
    db.add(conversion)
    try:
        await db.commit()
        await db.refresh(conversion)
    except IntegrityError:
        await db.rollback()
        raise DuplicateError("UomConversion")

    return conversion


async def get_conversions(
    db: AsyncSession, uom_id: int, page: int = 1, page_size: int = 50
) -> PaginatedResponse[UomConversionResponse]:
    """Get all conversions for a given unit.

    Args:
        db: Database session.
        uom_id: Unit ID to get conversions for.
        page: Page number.
        page_size: Items per page.
    Returns:
        PaginatedResponse of UomConversionResponse items.
    """
    query = select(UomConversion).where(
        or_(
            UomConversion.from_uom_id == uom_id,
            UomConversion.to_uom_id == uom_id
        )
    )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    query = query.order_by(UomConversion.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[UomConversionResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )


async def _get_all_conversions_graph(db: AsyncSession) -> dict[int, list[tuple[int, Decimal]]]:
    """Helper to build a graph of all conversions."""
    query = select(UomConversion)
    result = await db.execute(query)
    conversions = result.scalars().all()

    graph: dict[int, list[tuple[int, Decimal]]] = {}
    for conv in conversions:
        if conv.from_uom_id not in graph:
            graph[conv.from_uom_id] = []
        if conv.to_uom_id not in graph:
            graph[conv.to_uom_id] = []

        # Add forward edge
        graph[conv.from_uom_id].append((conv.to_uom_id, Decimal(str(conv.factor))))
        # Add backward edge
        graph[conv.to_uom_id].append((conv.from_uom_id, Decimal('1') / Decimal(str(conv.factor))))

    return graph

async def _get_uom_codes(db: AsyncSession, ids: list[int]) -> dict[int, str]:
    query = select(UnitOfMeasure).where(UnitOfMeasure.id.in_(ids))
    result = await db.execute(query)
    uoms = result.scalars().all()
    return {uom.id: uom.code for uom in uoms}

async def convert_quantity(db: AsyncSession, request: UomConvertRequest) -> UomConvertResponse:
    """Convert a quantity from one unit to another.

    Supports transitive conversions: if direct A->B is not defined but
    A->C and C->B exist, the conversion is computed via the intermediate.
    Uses BFS/DFS to find the shortest conversion path.

    Args:
        db: Database session.
        request: Conversion request with from, to, and quantity.
    Returns:
        UomConvertResponse with converted value and conversion path.
    Raises:
        NotFoundError: If units do not exist.
        BusinessRuleError: If no conversion path exists.
    """
    if request.from_uom_id == request.to_uom_id:
        path = await _get_uom_codes(db, [request.from_uom_id])
        return UomConvertResponse(
            from_uom_id=request.from_uom_id,
            to_uom_id=request.to_uom_id,
            input_quantity=request.quantity,
            converted_quantity=request.quantity,
            factor_used=Decimal('1'),
            conversion_path=[path.get(request.from_uom_id, str(request.from_uom_id))]
        )

    # Validate existance of both units
    from_uom_res = await db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == request.from_uom_id))
    if not from_uom_res.scalar_one_or_none():
        raise NotFoundError("UnitOfMeasure", str(request.from_uom_id))

    to_uom_res = await db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == request.to_uom_id))
    if not to_uom_res.scalar_one_or_none():
        raise NotFoundError("UnitOfMeasure", str(request.to_uom_id))

    graph = await _get_all_conversions_graph(db)

    if request.from_uom_id not in graph:
        raise BusinessRuleError("No conversion path exists.")

    # BFS
    queue: deque[tuple[int, Decimal, list[int]]] = deque([(request.from_uom_id, Decimal('1'), [request.from_uom_id])])
    visited = {request.from_uom_id}

    while queue:
        current_node, current_factor, path = queue.popleft()

        if current_node == request.to_uom_id:
            # We found a path
            uom_codes = await _get_uom_codes(db, path)
            code_path = [uom_codes.get(p, str(p)) for p in path]
            return UomConvertResponse(
                from_uom_id=request.from_uom_id,
                to_uom_id=request.to_uom_id,
                input_quantity=request.quantity,
                converted_quantity=request.quantity * current_factor,
                factor_used=current_factor,
                conversion_path=code_path
            )

        for neighbor, factor in graph.get(current_node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, current_factor * factor, path + [neighbor]))

    raise BusinessRuleError("No conversion path exists.")


async def get_compatible_uoms(db: AsyncSession, uom_id: int) -> list[UomResponse]:
    """Get all units that can be converted to/from the given unit.

    Uses graph traversal to find all reachable units through conversion chains.

    Args:
        db: Database session.
        uom_id: Unit ID to find compatible units for.
    Returns:
        List of compatible UomResponse items.
    Raises:
        NotFoundError: If the unit does not exist.
    """
    uom_res = await db.execute(select(UnitOfMeasure).where(UnitOfMeasure.id == uom_id))
    if not uom_res.scalar_one_or_none():
        raise NotFoundError("UnitOfMeasure", str(uom_id))

    graph = await _get_all_conversions_graph(db)

    reachable_ids = set()
    if uom_id in graph:
        # BFS
        queue = deque([uom_id])
        visited = {uom_id}

        while queue:
            current = queue.popleft()
            for neighbor, _ in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    reachable_ids.add(neighbor)
                    queue.append(neighbor)

    # Even if no conversions, unit is compatible with itself
    reachable_ids.add(uom_id)

    query = select(UnitOfMeasure).where(UnitOfMeasure.id.in_(reachable_ids))
    result = await db.execute(query)
    uoms = result.scalars().all()

    return [UomResponse.model_validate(uom) for uom in uoms]

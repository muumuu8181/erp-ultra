"""
Service logic for Sales Commission module.
"""
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError
from .models import Commission
from .schemas import CommissionCreate, CommissionUpdate
from .validators import validate_commission_create, validate_commission_update

async def create_commission(db: AsyncSession, data: CommissionCreate) -> Commission:
    """Create a new sales commission."""
    validate_commission_create(data)
    commission = Commission(**data.model_dump())
    db.add(commission)
    await db.commit()
    await db.refresh(commission)
    return commission

async def get_commission(db: AsyncSession, commission_id: int) -> Commission:
    """Get a sales commission by ID."""
    result = await db.execute(select(Commission).where(Commission.id == commission_id))
    commission = result.scalar_one_or_none()
    if not commission:
        raise NotFoundError("Commission", str(commission_id))
    return commission

async def update_commission(db: AsyncSession, commission_id: int, data: CommissionUpdate) -> Commission:
    """Update a sales commission."""
    validate_commission_update(data)
    commission = await get_commission(db, commission_id)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(commission, key, value)

    await db.commit()
    await db.refresh(commission)
    return commission

async def delete_commission(db: AsyncSession, commission_id: int) -> bool:
    """Delete a sales commission."""
    commission = await get_commission(db, commission_id)
    await db.delete(commission)
    await db.commit()
    return True

async def list_commissions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    salesperson_id: int | None = None
) -> tuple[Sequence[Commission], int]:
    """List sales commissions with optional filtering."""
    query = select(Commission)
    if salesperson_id is not None:
        query = query.where(Commission.salesperson_id == salesperson_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all(), total

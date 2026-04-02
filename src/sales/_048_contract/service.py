"""
Business logic and service layer for Contract Management.
"""
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError, DuplicateError
from src.sales._048_contract.models import Contract
from src.sales._048_contract.schemas import ContractCreate, ContractUpdate
from src.sales._048_contract.validators import validate_contract_create, validate_contract_update


async def create_contract(db: AsyncSession, data: ContractCreate) -> Contract:
    """
    Create a new contract.

    Raises:
        ValidationError: If business rules fail.
        DuplicateError: If contract number already exists.
    """
    validate_contract_create(data)

    # Check for duplicate contract number
    stmt = select(Contract).where(Contract.contract_number == data.contract_number)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise DuplicateError("Contract", key=data.contract_number)

    contract = Contract(**data.model_dump())
    db.add(contract)
    await db.flush()
    await db.refresh(contract)
    return contract


async def get_contract(db: AsyncSession, contract_id: int) -> Contract:
    """
    Retrieve a contract by ID.

    Raises:
        NotFoundError: If contract does not exist or is soft-deleted.
    """
    stmt = select(Contract).where(Contract.id == contract_id, Contract.is_deleted == False)
    contract = (await db.execute(stmt)).scalar_one_or_none()

    if not contract:
        raise NotFoundError("Contract", str(contract_id))

    return contract


async def list_contracts(
    db: AsyncSession, skip: int = 0, limit: int = 50
) -> tuple[Sequence[Contract], int]:
    """
    List contracts with pagination, filtering out soft-deleted records.

    Returns:
        A tuple of (contracts_list, total_count).
    """
    count_stmt = select(func.count()).select_from(Contract).where(Contract.is_deleted == False)
    total = (await db.execute(count_stmt)).scalar_one() or 0

    stmt = select(Contract).where(Contract.is_deleted == False).offset(skip).limit(limit)
    result = await db.execute(stmt)
    contracts = result.scalars().all()

    return contracts, total


async def update_contract(
    db: AsyncSession, contract_id: int, data: ContractUpdate
) -> Contract:
    """
    Update an existing contract.

    Raises:
        NotFoundError: If contract does not exist.
        ValidationError: If business rules fail.
    """
    contract = await get_contract(db, contract_id)

    validate_contract_update(data, contract.start_date, contract.end_date)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contract, key, value)

    await db.flush()
    await db.refresh(contract)
    return contract


async def delete_contract(db: AsyncSession, contract_id: int) -> None:
    """
    Soft delete a contract by ID.

    Raises:
        NotFoundError: If contract does not exist.
    """
    contract = await get_contract(db, contract_id)
    contract.is_deleted = True
    await db.flush()

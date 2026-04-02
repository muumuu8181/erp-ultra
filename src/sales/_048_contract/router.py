"""
FastAPI routes for Contract Management.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database import get_db
from src.sales._048_contract import service
from src.sales._048_contract.schemas import (
    ContractCreate,
    ContractUpdate,
    ContractRead,
    PaginatedContractResponse,
)

router = APIRouter(prefix="/api/v1/sales/contracts", tags=["sales", "contracts"])


@router.post("", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: ContractCreate, db: AsyncSession = Depends(get_db)
) -> ContractRead:
    """Create a new contract."""
    contract = await service.create_contract(db, data)
    return ContractRead.model_validate(contract)


@router.get("/{contract_id}", response_model=ContractRead)
async def get_contract(
    contract_id: int, db: AsyncSession = Depends(get_db)
) -> ContractRead:
    """Get a contract by ID."""
    contract = await service.get_contract(db, contract_id)
    return ContractRead.model_validate(contract)


@router.get("", response_model=PaginatedContractResponse)
async def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> PaginatedContractResponse:
    """List contracts with pagination."""
    skip = (page - 1) * page_size
    contracts, total = await service.list_contracts(db, skip=skip, limit=page_size)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedContractResponse(
        items=[ContractRead.model_validate(c) for c in contracts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.put("/{contract_id}", response_model=ContractRead)
async def update_contract(
    contract_id: int, data: ContractUpdate, db: AsyncSession = Depends(get_db)
) -> ContractRead:
    """Update an existing contract."""
    contract = await service.update_contract(db, contract_id, data)
    return ContractRead.model_validate(contract)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a contract."""
    await service.delete_contract(db, contract_id)

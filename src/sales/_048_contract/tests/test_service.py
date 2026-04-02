"""
Tests for Contract service layer.
"""
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import NotFoundError, DuplicateError, ValidationError
from src.sales._048_contract import service
from src.sales._048_contract.schemas import ContractCreate, ContractUpdate, ContractStatus


@pytest.fixture
def create_data():
    return ContractCreate(
        contract_number="CONT-SRV-001",
        customer_id=1,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        total_value=Decimal("1000.00"),
    )


@pytest.mark.asyncio
async def test_create_contract(db_session: AsyncSession, create_data: ContractCreate):
    contract = await service.create_contract(db_session, create_data)

    assert contract.id is not None
    assert contract.contract_number == "CONT-SRV-001"
    assert contract.status == "draft"


@pytest.mark.asyncio
async def test_create_contract_duplicate(db_session: AsyncSession, create_data: ContractCreate):
    await service.create_contract(db_session, create_data)

    with pytest.raises(DuplicateError):
        await service.create_contract(db_session, create_data)


@pytest.mark.asyncio
async def test_get_contract(db_session: AsyncSession, create_data: ContractCreate):
    created = await service.create_contract(db_session, create_data)

    fetched = await service.get_contract(db_session, created.id)
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_contract_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await service.get_contract(db_session, 9999)


@pytest.mark.asyncio
async def test_list_contracts(db_session: AsyncSession, create_data: ContractCreate):
    await service.create_contract(db_session, create_data)

    create_data_2 = create_data.model_copy(update={"contract_number": "CONT-SRV-002"})
    await service.create_contract(db_session, create_data_2)

    contracts, total = await service.list_contracts(db_session)
    assert total >= 2
    assert len(contracts) >= 2


@pytest.mark.asyncio
async def test_update_contract(db_session: AsyncSession, create_data: ContractCreate):
    created = await service.create_contract(db_session, create_data)

    update_data = ContractUpdate(status=ContractStatus.ACTIVE, total_value=Decimal("1500.00"))
    updated = await service.update_contract(db_session, created.id, update_data)

    assert updated.status == "active"
    assert updated.total_value == Decimal("1500.00")


@pytest.mark.asyncio
async def test_delete_contract(db_session: AsyncSession, create_data: ContractCreate):
    created = await service.create_contract(db_session, create_data)

    await service.delete_contract(db_session, created.id)

    # Verify soft delete behavior - getting should now raise NotFoundError
    with pytest.raises(NotFoundError):
        await service.get_contract(db_session, created.id)

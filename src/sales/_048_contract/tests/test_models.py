"""
Tests for Contract models.
"""
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.sales._048_contract.models import Contract


@pytest.mark.asyncio
async def test_contract_model_creation(db_session: AsyncSession):
    contract = Contract(
        contract_number="CONT-001",
        customer_id=1,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        status="draft",
        total_value=Decimal("10000.00"),
        terms="Standard terms apply."
    )
    db_session.add(contract)
    await db_session.flush()

    assert contract.id is not None
    assert contract.contract_number == "CONT-001"
    assert contract.customer_id == 1
    assert contract.start_date == date(2023, 1, 1)
    assert contract.end_date == date(2023, 12, 31)
    assert contract.status == "draft"
    assert contract.total_value == Decimal("10000.00")
    assert contract.terms == "Standard terms apply."
    assert contract.is_deleted is False


@pytest.mark.asyncio
async def test_contract_unique_number(db_session: AsyncSession):
    contract1 = Contract(
        contract_number="CONT-UNIQUE",
        customer_id=1,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        total_value=Decimal("10000.00")
    )
    db_session.add(contract1)
    await db_session.flush()

    contract2 = Contract(
        contract_number="CONT-UNIQUE",
        customer_id=2,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        total_value=Decimal("5000.00")
    )
    db_session.add(contract2)

    with pytest.raises(IntegrityError):
        await db_session.flush()

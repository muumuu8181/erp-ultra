import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from sales._042_commission.service import create_commission, get_commission, update_commission, delete_commission, list_commissions
from sales._042_commission.schemas import CommissionCreate, CommissionUpdate
from shared.errors import NotFoundError

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.mark.asyncio
async def test_create_commission(mock_db):
    data = CommissionCreate(
        salesperson_id=1,
        sales_order_id=2,
        commission_rate=Decimal("10.5"),
        amount=Decimal("100.00"),
        calculation_date=date(2023, 1, 1)
    )
    commission = await create_commission(mock_db, data)
    assert commission.salesperson_id == 1
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_commission(mock_db):
    mock_result = MagicMock()
    mock_commission = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_commission
    mock_db.execute.return_value = mock_result

    result = await get_commission(mock_db, 1)
    assert result == mock_commission
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_commission_not_found(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(NotFoundError):
        await get_commission(mock_db, 1)

@pytest.mark.asyncio
async def test_update_commission(mock_db):
    mock_result = MagicMock()
    mock_commission = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_commission
    mock_db.execute.return_value = mock_result

    data = CommissionUpdate(amount=Decimal("200.00"))
    result = await update_commission(mock_db, 1, data)

    assert result == mock_commission
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_delete_commission(mock_db):
    mock_result = MagicMock()
    mock_commission = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_commission
    mock_db.execute.return_value = mock_result

    result = await delete_commission(mock_db, 1)

    assert result is True
    mock_db.delete.assert_called_once_with(mock_commission)
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_list_commissions(mock_db):
    mock_result = MagicMock()
    mock_total_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [MagicMock()]
    mock_total_result.scalar_one.return_value = 1
    mock_db.execute.side_effect = [mock_total_result, mock_result]

    items, total = await list_commissions(mock_db)

    assert total == 1
    assert len(items) == 1
    assert mock_db.execute.call_count == 2

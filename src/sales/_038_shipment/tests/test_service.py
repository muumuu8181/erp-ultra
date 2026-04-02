import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from src.sales._038_shipment.schemas import ShipmentCreate, ShipmentItemCreate, ShipmentUpdate
from src.sales._038_shipment.service import create_shipment, get_shipment, update_shipment, delete_shipment
from shared.errors import NotFoundError

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db

@pytest.mark.asyncio
async def test_create_shipment(mock_db):
    data = ShipmentCreate(
        sales_order_id=1,
        customer_id=1,
        status="draft",
        items=[ShipmentItemCreate(product_id=1, quantity=Decimal("10.0"))]
    )

    mock_scalar = MagicMock()
    mock_scalar.id = 1
    mock_scalar.sales_order_id = 1
    mock_scalar.items = [MagicMock(product_id=1, quantity=Decimal("10.0"))]

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_scalar
    mock_db.execute.return_value = mock_result

    shipment = await create_shipment(mock_db, data)
    assert shipment.sales_order_id == 1
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_shipment_not_found(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(NotFoundError):
        await get_shipment(mock_db, 999)

@pytest.mark.asyncio
async def test_update_shipment(mock_db):
    mock_shipment = MagicMock()
    mock_shipment.id = 1
    mock_shipment.status = "draft"

    # get_shipment
    mock_result1 = MagicMock()
    mock_result1.scalar_one_or_none.return_value = mock_shipment

    # second execute inside update
    mock_result2 = MagicMock()
    mock_result2.scalar_one.return_value = mock_shipment

    mock_db.execute.side_effect = [mock_result1, mock_result2]

    data = ShipmentUpdate(status="shipped")
    updated = await update_shipment(mock_db, 1, data)

    assert updated.status == "shipped"
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_shipment(mock_db):
    mock_shipment = MagicMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_shipment
    mock_db.execute.return_value = mock_result

    await delete_shipment(mock_db, 1)
    mock_db.delete.assert_called_once_with(mock_shipment)
    mock_db.commit.assert_called_once()

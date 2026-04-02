import pytest
from decimal import Decimal

from shared.types import DocumentStatus
from src.sales._037_sales_order.models import SalesOrder, SalesOrderItem

@pytest.mark.asyncio
async def test_sales_order_creation(in_memory_db):
    so = SalesOrder(
        code="SO-TEST-001",
        customer_id=1,
        total_amount=Decimal("100.50")
    )
    in_memory_db.add(so)
    await in_memory_db.commit()
    await in_memory_db.refresh(so)

    assert so.id is not None
    assert so.status == DocumentStatus.DRAFT.value
    assert so.code == "SO-TEST-001"

@pytest.mark.asyncio
async def test_sales_order_item_creation(in_memory_db):
    so = SalesOrder(
        code="SO-TEST-002",
        customer_id=1,
        total_amount=Decimal("20.00")
    )
    in_memory_db.add(so)
    await in_memory_db.commit()
    await in_memory_db.refresh(so)

    item = SalesOrderItem(
        sales_order_id=so.id,
        product_id=10,
        quantity=Decimal("2"),
        unit_price=Decimal("10.00")
    )
    in_memory_db.add(item)
    await in_memory_db.commit()
    await in_memory_db.refresh(item)

    assert item.id is not None
    assert item.product_id == 10

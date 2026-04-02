import pytest
from decimal import Decimal

from shared.errors import NotFoundError
from shared.types import DocumentStatus
from src.sales._037_sales_order import service
from src.sales._037_sales_order.schemas import SalesOrderCreate, SalesOrderItemCreate, SalesOrderUpdate

@pytest.mark.asyncio
async def test_create_sales_order(in_memory_db):
    data = SalesOrderCreate(
        customer_id=1,
        items=[
            SalesOrderItemCreate(product_id=10, quantity=Decimal("2"), unit_price=Decimal("50.00")),
            SalesOrderItemCreate(product_id=20, quantity=Decimal("1"), unit_price=Decimal("100.00"))
        ]
    )
    order = await service.create_sales_order(in_memory_db, data)
    assert order.id is not None
    assert order.customer_id == 1
    assert order.total_amount == Decimal("200.00")
    assert len(order.items) == 2

@pytest.mark.asyncio
async def test_get_sales_order(in_memory_db):
    data = SalesOrderCreate(
        customer_id=1,
        items=[SalesOrderItemCreate(product_id=10, quantity=Decimal("2"), unit_price=Decimal("50.00"))]
    )
    created = await service.create_sales_order(in_memory_db, data)

    fetched = await service.get_sales_order(in_memory_db, created.id)
    assert fetched.id == created.id
    assert fetched.code == created.code

@pytest.mark.asyncio
async def test_get_sales_order_not_found(in_memory_db):
    with pytest.raises(NotFoundError):
        await service.get_sales_order(in_memory_db, 999)

@pytest.mark.asyncio
async def test_list_sales_orders(in_memory_db):
    data1 = SalesOrderCreate(customer_id=1, items=[SalesOrderItemCreate(product_id=10, quantity=Decimal("2"), unit_price=Decimal("50.00"))])
    data2 = SalesOrderCreate(customer_id=2, items=[SalesOrderItemCreate(product_id=10, quantity=Decimal("2"), unit_price=Decimal("50.00"))])

    await service.create_sales_order(in_memory_db, data1)
    await service.create_sales_order(in_memory_db, data2)

    items, total, page, total_pages = await service.list_sales_orders(in_memory_db)
    assert total >= 2
    assert len(items) >= 2

@pytest.mark.asyncio
async def test_update_sales_order_status(in_memory_db):
    data = SalesOrderCreate(
        customer_id=1,
        items=[SalesOrderItemCreate(product_id=10, quantity=Decimal("2"), unit_price=Decimal("50.00"))]
    )
    created = await service.create_sales_order(in_memory_db, data)

    update_data = SalesOrderUpdate(status=DocumentStatus.APPROVED)
    updated = await service.update_sales_order_status(in_memory_db, created.id, update_data)

    assert updated.status == DocumentStatus.APPROVED.value

@pytest.mark.asyncio
async def test_delete_sales_order(in_memory_db):
    data = SalesOrderCreate(
        customer_id=1,
        items=[SalesOrderItemCreate(product_id=10, quantity=Decimal("2"), unit_price=Decimal("50.00"))]
    )
    created = await service.create_sales_order(in_memory_db, data)

    await service.delete_sales_order(in_memory_db, created.id)

    with pytest.raises(NotFoundError):
        await service.get_sales_order(in_memory_db, created.id)

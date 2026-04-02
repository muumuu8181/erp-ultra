"""
Sales Order Router
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database import get_db
from src.sales._037_sales_order import service
from src.sales._037_sales_order.schemas import (
    SalesOrderCreate,
    SalesOrderResponse,
    SalesOrderUpdate,
    SalesOrderPaginatedResponse,
)

router = APIRouter(prefix="/api/v1/sales-orders", tags=["Sales Orders"])


@router.post("/", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_sales_order(
    data: SalesOrderCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new sales order."""
    return await service.create_sales_order(db, data)


@router.get("/{order_id}", response_model=SalesOrderResponse)
async def get_sales_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a sales order by ID."""
    return await service.get_sales_order(db, order_id)


@router.get("/", response_model=SalesOrderPaginatedResponse)
async def list_sales_orders(
    page: int = 1, page_size: int = 50, db: AsyncSession = Depends(get_db)
):
    """List sales orders."""
    items, total, page_num, total_pages = await service.list_sales_orders(
        db, page=page, page_size=page_size
    )
    return {
        "items": items,
        "total": total,
        "page": page_num,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.patch("/{order_id}/status", response_model=SalesOrderResponse)
async def update_sales_order_status(
    order_id: int, data: SalesOrderUpdate, db: AsyncSession = Depends(get_db)
):
    """Update sales order status."""
    return await service.update_sales_order_status(db, order_id, data)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sales_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a sales order."""
    await service.delete_sales_order(db, order_id)

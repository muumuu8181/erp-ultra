"""
Stock Transfer router.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import BusinessRuleError, ValidationError
from shared.types import PaginatedResponse
from src.foundation._001_database.engine import get_db
from src.inventory._053_stock_transfer.schemas import (
    ReceiveLineInput,
    StockTransferCreate,
    StockTransferResponse,
    StockTransferUpdate,
)
from src.inventory._053_stock_transfer.service import (
    cancel_transfer,
    create_transfer,
    dispatch,
    get_in_transit,
    get_transfer,
    list_transfers,
    receive_transfer,
    update_transfer,
)

router = APIRouter(prefix="/api/v1/stock-transfers", tags=["stock-transfers"])


@router.post("", response_model=StockTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer_endpoint(
    data: StockTransferCreate,
    db: AsyncSession = Depends(get_db)
) -> StockTransferResponse:
    """Create a new stock transfer."""
    try:
        transfer = await create_transfer(db, data)
        return StockTransferResponse.model_validate(transfer)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PaginatedResponse[StockTransferResponse])
async def list_transfers_endpoint(
    from_warehouse: Optional[str] = Query(None),
    to_warehouse: Optional[str] = Query(None),
    transfer_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[StockTransferResponse]:
    """List stock transfers with pagination and filters."""
    result = await list_transfers(
        db=db,
        from_warehouse=from_warehouse,
        to_warehouse=to_warehouse,
        status=transfer_status,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse[StockTransferResponse](
        items=[StockTransferResponse.model_validate(item) for item in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages
    )


@router.get("/in-transit", response_model=List[StockTransferResponse])
async def get_in_transit_endpoint(
    warehouse_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> List[StockTransferResponse]:
    """List all in-transit transfers."""
    transfers = await get_in_transit(db, warehouse_code)
    return [StockTransferResponse.model_validate(transfer) for transfer in transfers]


@router.get("/{transfer_id}", response_model=StockTransferResponse)
async def get_transfer_endpoint(
    transfer_id: int,
    db: AsyncSession = Depends(get_db)
) -> StockTransferResponse:
    """Get a stock transfer by ID."""
    transfer = await get_transfer(db, transfer_id)
    return StockTransferResponse.model_validate(transfer)


@router.put("/{transfer_id}", response_model=StockTransferResponse)
async def update_transfer_endpoint(
    transfer_id: int,
    data: StockTransferUpdate,
    db: AsyncSession = Depends(get_db)
) -> StockTransferResponse:
    """Update a draft stock transfer."""
    transfer = await update_transfer(db, transfer_id, data)
    return StockTransferResponse.model_validate(transfer)


@router.post("/{transfer_id}/dispatch", response_model=StockTransferResponse)
async def dispatch_endpoint(
    transfer_id: int,
    db: AsyncSession = Depends(get_db)
) -> StockTransferResponse:
    """Dispatch a stock transfer."""
    transfer = await dispatch(db, transfer_id)
    return StockTransferResponse.model_validate(transfer)


@router.post("/{transfer_id}/receive", response_model=StockTransferResponse)
async def receive_endpoint(
    transfer_id: int,
    received_lines: List[ReceiveLineInput],
    db: AsyncSession = Depends(get_db)
) -> StockTransferResponse:
    """Receive a stock transfer."""
    transfer = await receive_transfer(db, transfer_id, received_lines)
    return StockTransferResponse.model_validate(transfer)


@router.post("/{transfer_id}/cancel", response_model=StockTransferResponse)
async def cancel_endpoint(
    transfer_id: int,
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> StockTransferResponse:
    """Cancel a draft stock transfer."""
    transfer = await cancel_transfer(db, transfer_id, reason)
    return StockTransferResponse.model_validate(transfer)

"""
FastAPI router for inventory valuation.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, ValidationError, NotFoundError, CalculationError
from src.foundation._001_database import get_db
from src.inventory._061_inventory_valuation import service
from src.inventory._061_inventory_valuation.schemas import (
    ValuationMethodCreate,
    ValuationMethodResponse,
    CostLayerCreate,
    CostLayerResponse,
    ValuationSnapshotResponse,
    ValuationReport,
    ValuationSummary,
    CalculateValuationRequest,
    GenerateSnapshotRequest,
    ConsumeCostLayerRequest
)
from src.inventory._061_inventory_valuation.validators import validate_one_method_per_product

router = APIRouter(prefix="/api/v1/inventory-valuation", tags=["Inventory Valuation"])


@router.post("/valuation-methods", response_model=ValuationMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_valuation_method(data: ValuationMethodCreate, db: AsyncSession = Depends(get_db)):
    """Set the valuation method for a product."""
    try:
        await validate_one_method_per_product(db, data.product_code)
    except DuplicateError:
        pass # Service will deactivate the old one

    method = await service.set_valuation_method(db, data)
    return method


@router.get("/valuation-methods", response_model=ValuationMethodResponse)
async def get_valuation_method(product_code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Get active valuation method for a product."""
    return await service.get_valuation_method(db, product_code)


@router.post("/cost-layers", response_model=CostLayerResponse, status_code=status.HTTP_201_CREATED)
async def create_cost_layer(data: CostLayerCreate, db: AsyncSession = Depends(get_db)):
    """Add a new cost layer."""
    layer = await service.add_cost_layer(
        db,
        product_code=data.product_code,
        warehouse_code=data.warehouse_code,
        received_date=data.received_date,
        quantity=data.quantity,
        unit_cost=data.unit_cost
    )
    return layer


@router.post("/cost-layers/consume", response_model=list[CostLayerResponse])
async def consume_cost_layer(data: ConsumeCostLayerRequest, db: AsyncSession = Depends(get_db)):
    """Consume cost layers."""
    method = await service.get_valuation_method(db, data.product_code)
    return await service.consume_cost_layer(
        db,
        product_code=data.product_code,
        warehouse_code=data.warehouse_code,
        quantity=data.quantity,
        method=method.method
    )


@router.get("/cost-layers", response_model=list[CostLayerResponse])
async def list_cost_layers(
    product_code: Optional[str] = Query(None),
    warehouse_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List cost layers."""
    return await service.get_cost_layers(db, product_code, warehouse_code)


@router.post("/calculate", response_model=list[ValuationSnapshotResponse])
async def calculate_valuation(data: CalculateValuationRequest, db: AsyncSession = Depends(get_db)):
    """Calculate current valuation for a product."""
    return await service.calculate_valuation(db, data.product_code, data.warehouse_code)


@router.post("/snapshot", response_model=list[ValuationSnapshotResponse])
async def generate_snapshot(data: GenerateSnapshotRequest, db: AsyncSession = Depends(get_db)):
    """Generate valuation snapshot."""
    return await service.generate_snapshot(db, data.snapshot_date)


@router.get("/report", response_model=ValuationReport)
async def get_valuation_report(
    product_code: Optional[str] = Query(None),
    warehouse_code: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get valuation report."""
    return await service.get_valuation_report(db, product_code, warehouse_code, category)


@router.get("/summary", response_model=ValuationSummary)
async def get_valuation_summary(db: AsyncSession = Depends(get_db)):
    """Get valuation summary."""
    return await service.get_valuation_summary(db)

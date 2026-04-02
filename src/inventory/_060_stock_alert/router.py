from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.foundation._001_database.engine import get_db
from shared.types import PaginatedResponse
from shared.errors import NotFoundError, ValidationError

from src.inventory._060_stock_alert.schemas import (
    AlertRuleCreate,
    AlertRuleResponse,
    StockAlertResponse,
    AlertAcknowledge,
    AlertStats,
)
from src.inventory._060_stock_alert.models import AlertRule
from src.inventory._060_stock_alert import service


router = APIRouter(prefix="/api/v1/stock-alert", tags=["Stock Alert"])


@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    data: AlertRuleCreate, db: AsyncSession = Depends(get_db)
):
    try:
        rule = await service.create_rule(db, data)
        return rule
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/alert-rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRule))
    rules = result.scalars().all()
    return rules


@router.put("/alert-rules/{id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    id: int, data: dict, db: AsyncSession = Depends(get_db)
):
    try:
        rule = await service.update_rule(db, id, data)
        return rule
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/stock-alerts/evaluate", response_model=List[StockAlertResponse])
async def evaluate_stock_alerts(
    warehouse_code: str | None = None, db: AsyncSession = Depends(get_db)
):
    alerts = await service.evaluate_rules(db, warehouse_code)
    return alerts


@router.get("/stock-alerts", response_model=PaginatedResponse[StockAlertResponse])
async def list_stock_alerts(
    status: str | None = None,
    alert_type: str | None = None,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await service.get_alerts(
        db,
        status=status,
        alert_type=alert_type,
        severity=severity,
        page=page,
        page_size=page_size,
    )


@router.post("/stock-alerts/{id}/acknowledge", response_model=StockAlertResponse)
async def acknowledge_stock_alert(
    id: int, data: AlertAcknowledge, db: AsyncSession = Depends(get_db)
):
    try:
        alert = await service.acknowledge_alert(db, id, data.acknowledged_by)
        return alert
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/stock-alerts/{id}/resolve", response_model=StockAlertResponse)
async def resolve_stock_alert(id: int, db: AsyncSession = Depends(get_db)):
    try:
        alert = await service.resolve_alert(db, id)
        return alert
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stock-alerts/stats", response_model=AlertStats)
async def get_stock_alert_stats(
    warehouse_code: str | None = None, db: AsyncSession = Depends(get_db)
):
    return await service.get_stats(db, warehouse_code)


@router.delete("/stock-alerts/cleanup")
async def cleanup_stock_alerts(days: int = 90, db: AsyncSession = Depends(get_db)):
    deleted_count = await service.cleanup_old_alerts(db, days)
    return {"deleted_count": deleted_count}

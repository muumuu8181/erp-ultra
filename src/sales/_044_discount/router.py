from typing import Any
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from shared.errors import NotFoundError, BusinessRuleError, DuplicateError, ValidationError
from src.sales._044_discount import service
from src.sales._044_discount.schemas import (
    DiscountRuleCreate,
    DiscountRuleResponse,
    DiscountUsageResponse,
    DiscountApplyRequest,
    DiscountApplyResponse,
)

router = APIRouter(prefix="/api/v1", tags=["discount-rules"])

@router.post("/discount-rules", response_model=DiscountRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_discount_rule(
    data: DiscountRuleCreate, db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        return await service.create_rule(db, data)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)

@router.get("/discount-rules", response_model=list[DiscountRuleResponse])
async def list_discount_rules(
    applies_to: str | None = None, db: AsyncSession = Depends(get_db)
) -> Any:
    return await service.list_active_discounts(db, applies_to)

@router.put("/discount-rules/{id}", response_model=DiscountRuleResponse)
async def update_discount_rule(
    id: int, data: dict[str, Any], db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        return await service.update_rule(db, id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DuplicateError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)

@router.post("/discounts/apply", response_model=DiscountApplyResponse)
async def apply_discounts(
    request: DiscountApplyRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    return await service.apply_discount(db, request)

@router.post("/discounts/validate", response_model=DiscountRuleResponse)
async def validate_discount(
    code: str, customer_code: str, order_amount: float, db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        return await service.validate_discount(db, code, customer_code, Decimal(str(order_amount)))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=e.message)

@router.get("/discount-rules/{id}/usage", response_model=list[DiscountUsageResponse])
async def get_discount_usage(
    id: int, db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        return await service.get_usage(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

@router.delete("/discount-rules/{id}", response_model=DiscountRuleResponse)
async def deactivate_discount_rule(
    id: int, db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        return await service.deactivate_rule(db, id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

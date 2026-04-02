from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from shared.errors import NotFoundError, ValidationError, DuplicateError
from . import service
from .schemas import (
    PromotionCreate,
    PromotionUpdate,
    PromotionResponse,
    PromotionEvaluateRequest,
    PromotionEvaluateResponse,
    PromotionRedemptionResponse,
    PromotionRedeemRequest
)

router = APIRouter(prefix="/api/v1/promotions", tags=["promotions"])

@router.post("", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
async def create_promotion_endpoint(
    data: PromotionCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        promotion = await service.create_promotion(db, data)
        return promotion
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("", response_model=List[PromotionResponse])
async def list_active_promotions_endpoint(db: AsyncSession = Depends(get_db)):
    promotions = await service.list_active(db)
    return promotions

@router.put("/{promotion_id}", response_model=PromotionResponse)
async def update_promotion_endpoint(
    promotion_id: int,
    data: PromotionUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        promotion = await service.update_promotion(db, promotion_id, data)
        return promotion
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/evaluate", response_model=PromotionEvaluateResponse)
async def evaluate_promotions_endpoint(
    request: PromotionEvaluateRequest,
    db: AsyncSession = Depends(get_db)
):
    response = await service.evaluate_promotions(db, request)
    return response

@router.post("/{promotion_id}/redeem", response_model=PromotionRedemptionResponse)
async def redeem_promotion_endpoint(
    promotion_id: int,
    request: PromotionRedeemRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        redemption = await service.redeem_promotion(
            db,
            promotion_id,
            request.order_number,
            request.customer_code,
            request.redeemed_value
        )
        return redemption
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{promotion_id}/redemptions", response_model=List[PromotionRedemptionResponse])
async def get_redemptions_endpoint(
    promotion_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        redemptions = await service.get_redemptions(db, promotion_id)
        return redemptions
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{promotion_id}", response_model=PromotionResponse)
async def deactivate_promotion_endpoint(
    promotion_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        promotion = await service.deactivate(db, promotion_id)
        return promotion
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

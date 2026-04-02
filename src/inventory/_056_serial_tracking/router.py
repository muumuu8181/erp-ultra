from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from src.foundation._001_database.engine import get_db
from .schemas import SerialCreate, SerialResponse, SerialTraceRequest, SerialTraceResponse, WarrantyCheck, WarrantyCheckResponse
from . import service

router = APIRouter(prefix="/api/v1/serials", tags=["Serial Tracking"])


@router.post("", response_model=SerialResponse, status_code=status.HTTP_201_CREATED)
async def register_serial(data: SerialCreate, db: AsyncSession = Depends(get_db)):
    serial = await service.register_serial(db, data)
    return serial


@router.get("", response_model=List[SerialResponse])
async def list_serials(db: AsyncSession = Depends(get_db)):
    # simple list, could be expanded with pagination/filters if necessary
    from sqlalchemy import select
    from .models import SerialNumber
    result = await db.execute(select(SerialNumber))
    return list(result.scalars().all())


@router.get("/by-product", response_model=List[SerialResponse])
async def get_by_product(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    return await service.get_by_product(db, code)


@router.get("/by-customer", response_model=List[SerialResponse])
async def get_by_customer(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    return await service.get_by_customer(db, code)


@router.get("/{id}", response_model=SerialResponse)
async def get_serial(id: int, db: AsyncSession = Depends(get_db)):
    return await service.get_serial(db, id)


class ReserveRequest(BaseModel):
    reference_type: str
    reference_number: str

@router.post("/{id}/reserve", response_model=SerialResponse)
async def reserve_serial(id: int, request: ReserveRequest, db: AsyncSession = Depends(get_db)):
    return await service.reserve(db, id, request.reference_type, request.reference_number)


class ShipRequest(BaseModel):
    customer_code: str
    sale_date: date
    reference_type: str
    reference_number: str

@router.post("/{id}/ship", response_model=SerialResponse)
async def ship_serial(id: int, request: ShipRequest, db: AsyncSession = Depends(get_db)):
    return await service.ship(db, id, request.customer_code, request.sale_date, request.reference_type, request.reference_number)


class ReturnRequest(BaseModel):
    reason: str
    reference_type: str
    reference_number: str

@router.post("/{id}/return", response_model=SerialResponse)
async def return_serial(id: int, request: ReturnRequest, db: AsyncSession = Depends(get_db)):
    return await service.return_serial(db, id, request.reason, request.reference_type, request.reference_number)


class TransferRequest(BaseModel):
    to_warehouse: str
    to_bin: Optional[str] = None
    reference_number: str

@router.post("/{id}/transfer", response_model=SerialResponse)
async def transfer_serial(id: int, request: TransferRequest, db: AsyncSession = Depends(get_db)):
    return await service.transfer(db, id, request.to_warehouse, request.to_bin, request.reference_number)


class ScrapRequest(BaseModel):
    reason: str
    reference_type: str
    reference_number: str

@router.post("/{id}/scrap", response_model=SerialResponse)
async def scrap_serial(id: int, request: ScrapRequest, db: AsyncSession = Depends(get_db)):
    return await service.scrap(db, id, request.reason, request.reference_type, request.reference_number)


@router.post("/trace", response_model=SerialTraceResponse)
async def trace_serial(request: SerialTraceRequest, db: AsyncSession = Depends(get_db)):
    return await service.trace_serial(db, request)


@router.post("/warranty-check", response_model=WarrantyCheckResponse)
async def check_warranty(request: WarrantyCheck, db: AsyncSession = Depends(get_db)):
    return await service.check_warranty(db, request)

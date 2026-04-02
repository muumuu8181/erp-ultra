from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime
from typing import List, Optional

from shared.errors import NotFoundError
from .models import SerialNumber, SerialHistory, SerialStatus, SerialEventType
from .schemas import SerialCreate, SerialTraceRequest, SerialTraceResponse, WarrantyCheck, WarrantyCheckResponse, TraceDirection, SerialHistoryResponse
from .validators import validate_serial_number_unique, validate_status_transition, validate_warranty_dates, validate_ship_requirements, validate_scrap


async def register_serial(db: AsyncSession, data: SerialCreate) -> SerialNumber:
    await validate_serial_number_unique(db, data.serial_number)
    validate_warranty_dates(data.warranty_start, data.warranty_end)

    status = SerialStatus.in_stock
    if data.status:
        status = SerialStatus(data.status)

    serial = SerialNumber(
        serial_number=data.serial_number,
        product_code=data.product_code,
        warehouse_code=data.warehouse_code,
        bin_code=data.bin_code,
        status=status,
        supplier_code=data.supplier_code,
        customer_code=data.customer_code,
        purchase_date=data.purchase_date,
        warranty_start=data.warranty_start,
        warranty_end=data.warranty_end,
        notes=data.notes
    )
    db.add(serial)
    await db.flush()

    history = SerialHistory(
        serial_id=serial.id,
        event_type=SerialEventType.received,
        reference_type="registration",
        reference_number="init",
        location_to=data.warehouse_code,
        event_date=datetime.now(),
        notes=data.notes
    )
    db.add(history)
    await db.commit()
    await db.refresh(serial)
    return serial


async def get_serial(db: AsyncSession, serial_id: int) -> SerialNumber:
    serial = await db.get(SerialNumber, serial_id)
    if not serial:
        raise NotFoundError("SerialNumber", str(serial_id))
    return serial


async def update_status(db: AsyncSession, serial_id: int, new_status: str, reference_type: str, reference_number: str, notes: Optional[str]) -> SerialNumber:
    serial = await get_serial(db, serial_id)
    target_status = SerialStatus(new_status)
    validate_status_transition(serial.status, target_status)

    serial.status = target_status

    event_type_map = {
        SerialStatus.in_stock: SerialEventType.stored,
        SerialStatus.reserved: SerialEventType.reserved,
        SerialStatus.shipped: SerialEventType.shipped,
        SerialStatus.in_repair: SerialEventType.repaired,
        SerialStatus.scrapped: SerialEventType.scrapped,
    }

    history = SerialHistory(
        serial_id=serial.id,
        event_type=event_type_map.get(target_status, SerialEventType.stored),
        reference_type=reference_type,
        reference_number=reference_number,
        event_date=datetime.now(),
        notes=notes
    )
    db.add(history)
    await db.commit()
    await db.refresh(serial)
    return serial


async def reserve(db: AsyncSession, serial_id: int, reference_type: str, reference_number: str) -> SerialNumber:
    return await update_status(db, serial_id, SerialStatus.reserved.value, reference_type, reference_number, notes="Reserved")


async def ship(db: AsyncSession, serial_id: int, customer_code: str, sale_date: date, reference_type: str, reference_number: str) -> SerialNumber:
    validate_ship_requirements(customer_code, sale_date)
    serial = await get_serial(db, serial_id)
    validate_status_transition(serial.status, SerialStatus.shipped)

    serial.status = SerialStatus.shipped
    serial.customer_code = customer_code
    serial.sale_date = sale_date

    history = SerialHistory(
        serial_id=serial.id,
        event_type=SerialEventType.shipped,
        reference_type=reference_type,
        reference_number=reference_number,
        event_date=datetime.now()
    )
    db.add(history)
    await db.commit()
    await db.refresh(serial)
    return serial


async def return_serial(db: AsyncSession, serial_id: int, reason: str, reference_type: str, reference_number: str) -> SerialNumber:
    serial = await get_serial(db, serial_id)
    validate_status_transition(serial.status, SerialStatus.in_stock)

    serial.status = SerialStatus.in_stock
    serial.customer_code = None
    serial.sale_date = None

    history = SerialHistory(
        serial_id=serial.id,
        event_type=SerialEventType.returned,
        reference_type=reference_type,
        reference_number=reference_number,
        event_date=datetime.now(),
        notes=reason
    )
    db.add(history)
    await db.commit()
    await db.refresh(serial)
    return serial


async def transfer(db: AsyncSession, serial_id: int, to_warehouse: str, to_bin: Optional[str], reference_number: str) -> SerialNumber:
    serial = await get_serial(db, serial_id)

    location_from_warehouse = serial.warehouse_code

    serial.warehouse_code = to_warehouse
    serial.bin_code = to_bin

    history = SerialHistory(
        serial_id=serial.id,
        event_type=SerialEventType.transferred,
        reference_type="transfer",
        reference_number=reference_number,
        location_from=location_from_warehouse,
        location_to=to_warehouse,
        event_date=datetime.now()
    )
    db.add(history)
    await db.commit()
    await db.refresh(serial)
    return serial


async def scrap(db: AsyncSession, serial_id: int, reason: str, reference_type: str, reference_number: str) -> SerialNumber:
    serial = await get_serial(db, serial_id)
    validate_scrap(serial.status)
    validate_status_transition(serial.status, SerialStatus.scrapped)

    serial.status = SerialStatus.scrapped

    history = SerialHistory(
        serial_id=serial.id,
        event_type=SerialEventType.scrapped,
        reference_type=reference_type,
        reference_number=reference_number,
        event_date=datetime.now(),
        notes=reason
    )
    db.add(history)
    await db.commit()
    await db.refresh(serial)
    return serial


async def trace_serial(db: AsyncSession, request: SerialTraceRequest) -> SerialTraceResponse:
    result = await db.execute(select(SerialNumber).where(SerialNumber.serial_number == request.serial_number))
    serial = result.scalars().first()
    if not serial:
        raise NotFoundError("SerialNumber", request.serial_number)

    order = SerialHistory.event_date.asc() if request.direction == TraceDirection.forward else SerialHistory.event_date.desc()
    histories_result = await db.execute(
        select(SerialHistory)
        .where(SerialHistory.serial_id == serial.id)
        .order_by(order)
    )
    histories = histories_result.scalars().all()

    history_responses = [SerialHistoryResponse.model_validate(h) for h in histories]

    return SerialTraceResponse(
        serial_number=serial.serial_number,
        product_code=serial.product_code,
        current_status=serial.status.value,
        history=history_responses
    )


async def check_warranty(db: AsyncSession, check: WarrantyCheck) -> WarrantyCheckResponse:
    result = await db.execute(select(SerialNumber).where(SerialNumber.serial_number == check.serial_number))
    serial = result.scalars().first()
    if not serial:
        raise NotFoundError("SerialNumber", check.serial_number)

    is_under_warranty = False
    days_remaining = None

    if serial.warranty_start and serial.warranty_end:
        if serial.warranty_start <= check.check_date <= serial.warranty_end:
            is_under_warranty = True
            days_remaining = (serial.warranty_end - check.check_date).days

    return WarrantyCheckResponse(
        serial_number=serial.serial_number,
        product_code=serial.product_code,
        is_under_warranty=is_under_warranty,
        warranty_start=serial.warranty_start,
        warranty_end=serial.warranty_end,
        days_remaining=days_remaining
    )


async def get_by_product(db: AsyncSession, product_code: str) -> List[SerialNumber]:
    result = await db.execute(select(SerialNumber).where(SerialNumber.product_code == product_code))
    return list(result.scalars().all())


async def get_by_customer(db: AsyncSession, customer_code: str) -> List[SerialNumber]:
    result = await db.execute(select(SerialNumber).where(SerialNumber.customer_code == customer_code))
    return list(result.scalars().all())

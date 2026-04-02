from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.errors import DuplicateError, BusinessRuleError
from .models import SerialNumber, SerialStatus

VALID_TRANSITIONS = {
    SerialStatus.in_stock: {SerialStatus.reserved, SerialStatus.scrapped},
    SerialStatus.reserved: {SerialStatus.shipped, SerialStatus.in_stock},
    SerialStatus.shipped: {SerialStatus.in_stock, SerialStatus.in_repair},
    SerialStatus.in_repair: {SerialStatus.in_stock, SerialStatus.scrapped},
    SerialStatus.scrapped: set(),
}

async def validate_serial_number_unique(db: AsyncSession, serial_number: str) -> None:
    result = await db.execute(select(SerialNumber).where(SerialNumber.serial_number == serial_number))
    if result.scalars().first():
        raise DuplicateError("SerialNumber", serial_number)

def validate_status_transition(current_status: SerialStatus, new_status: SerialStatus) -> None:
    if current_status == SerialStatus.scrapped:
        raise BusinessRuleError("Cannot transition from scrapped status, it is a terminal state")

    if new_status not in VALID_TRANSITIONS.get(current_status, set()):
        raise BusinessRuleError(f"Invalid status transition from {current_status} to {new_status}")

def validate_warranty_dates(warranty_start: date | None, warranty_end: date | None) -> None:
    if warranty_start and warranty_end:
        if warranty_end <= warranty_start:
            raise BusinessRuleError("warranty_end must be > warranty_start")

def validate_ship_requirements(customer_code: str | None, sale_date: date | None) -> None:
    if not customer_code or not sale_date:
        raise BusinessRuleError("Cannot ship without customer_code and sale_date")

def validate_scrap(current_status: SerialStatus) -> None:
    if current_status == SerialStatus.scrapped:
        raise BusinessRuleError("Cannot scrap a serial that is already scrapped")

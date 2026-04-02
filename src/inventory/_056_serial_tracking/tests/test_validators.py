import pytest
from datetime import date
from shared.errors import DuplicateError, BusinessRuleError
from src.inventory._056_serial_tracking.models import SerialStatus, SerialNumber
from src.inventory._056_serial_tracking.validators import (
    validate_serial_number_unique,
    validate_status_transition,
    validate_warranty_dates,
    validate_ship_requirements,
    validate_scrap
)

@pytest.mark.asyncio
async def test_validate_serial_number_unique_success(db_session):
    # Setup - db is empty
    await validate_serial_number_unique(db_session, "NEW-SN")

@pytest.mark.asyncio
async def test_validate_serial_number_unique_failure(db_session):
    serial = SerialNumber(
        serial_number="EXISTING-SN",
        product_code="PROD-001",
        warehouse_code="WH-A",
        status=SerialStatus.in_stock
    )
    db_session.add(serial)
    await db_session.commit()

    with pytest.raises(DuplicateError):
        await validate_serial_number_unique(db_session, "EXISTING-SN")

def test_validate_status_transition_valid():
    validate_status_transition(SerialStatus.in_stock, SerialStatus.reserved)
    validate_status_transition(SerialStatus.reserved, SerialStatus.shipped)
    validate_status_transition(SerialStatus.shipped, SerialStatus.in_stock)
    validate_status_transition(SerialStatus.in_repair, SerialStatus.scrapped)

def test_validate_status_transition_invalid():
    with pytest.raises(BusinessRuleError):
        validate_status_transition(SerialStatus.in_stock, SerialStatus.shipped)

def test_validate_status_transition_terminal():
    with pytest.raises(BusinessRuleError):
        validate_status_transition(SerialStatus.scrapped, SerialStatus.in_stock)

def test_validate_warranty_dates():
    # Valid
    validate_warranty_dates(date(2023, 1, 1), date(2024, 1, 1))
    validate_warranty_dates(None, None)
    validate_warranty_dates(date(2023, 1, 1), None)

    # Invalid
    with pytest.raises(BusinessRuleError):
        validate_warranty_dates(date(2024, 1, 1), date(2023, 1, 1))

def test_validate_ship_requirements():
    validate_ship_requirements("CUST1", date(2023, 1, 1))

    with pytest.raises(BusinessRuleError):
        validate_ship_requirements(None, date(2023, 1, 1))

    with pytest.raises(BusinessRuleError):
        validate_ship_requirements("CUST1", None)

def test_validate_scrap():
    validate_scrap(SerialStatus.in_stock)

    with pytest.raises(BusinessRuleError):
        validate_scrap(SerialStatus.scrapped)

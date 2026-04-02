import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError
from src.inventory._056_serial_tracking.models import SerialNumber, SerialHistory, SerialStatus, SerialEventType

@pytest.mark.asyncio
async def test_serial_number_creation(db_session):
    serial = SerialNumber(
        serial_number="SN12345",
        product_code="PROD-001",
        warehouse_code="WH-A",
        status=SerialStatus.in_stock
    )
    db_session.add(serial)
    await db_session.commit()
    await db_session.refresh(serial)

    assert serial.id is not None
    assert serial.serial_number == "SN12345"

@pytest.mark.asyncio
async def test_serial_number_unique_constraint(db_session):
    serial1 = SerialNumber(
        serial_number="SN12345",
        product_code="PROD-001",
        warehouse_code="WH-A",
        status=SerialStatus.in_stock
    )
    db_session.add(serial1)
    await db_session.commit()

    serial2 = SerialNumber(
        serial_number="SN12345",
        product_code="PROD-002",
        warehouse_code="WH-B",
        status=SerialStatus.in_stock
    )
    db_session.add(serial2)
    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_serial_history_creation(db_session):
    serial = SerialNumber(
        serial_number="SN-HIST-001",
        product_code="PROD-001",
        warehouse_code="WH-A",
        status=SerialStatus.in_stock
    )
    db_session.add(serial)
    await db_session.commit()
    await db_session.refresh(serial)

    history = SerialHistory(
        serial_id=serial.id,
        event_type=SerialEventType.received,
        reference_type="registration",
        reference_number="ref1",
        event_date=datetime.now()
    )
    db_session.add(history)
    await db_session.commit()
    await db_session.refresh(history)

    assert history.id is not None

def test_status_enum_values():
    assert SerialStatus.in_stock == "in_stock"
    assert SerialStatus.reserved == "reserved"
    assert SerialStatus.shipped == "shipped"
    assert SerialStatus.in_repair == "in_repair"
    assert SerialStatus.scrapped == "scrapped"

def test_event_type_enum_values():
    assert SerialEventType.received == "received"
    assert SerialEventType.stored == "stored"
    assert SerialEventType.reserved == "reserved"
    assert SerialEventType.shipped == "shipped"
    assert SerialEventType.returned == "returned"
    assert SerialEventType.transferred == "transferred"
    assert SerialEventType.repaired == "repaired"
    assert SerialEventType.scrapped == "scrapped"

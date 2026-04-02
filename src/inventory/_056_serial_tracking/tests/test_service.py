import pytest
from datetime import date, datetime, timedelta
from shared.errors import NotFoundError, DuplicateError, BusinessRuleError
from src.inventory._056_serial_tracking.models import SerialNumber, SerialStatus, SerialHistory
from src.inventory._056_serial_tracking.schemas import SerialCreate, SerialTraceRequest, TraceDirection, WarrantyCheck
from src.inventory._056_serial_tracking.service import (
    register_serial, update_status, reserve, ship, return_serial, transfer, scrap,
    get_serial, trace_serial, check_warranty, get_by_product, get_by_customer
)
from sqlalchemy import select

@pytest.fixture
def sample_serial_data():
    return SerialCreate(
        serial_number="TEST-SN-001",
        product_code="PROD-1",
        warehouse_code="WH-1",
        status=SerialStatus.in_stock.value,
        warranty_start=date.today(),
        warranty_end=date.today() + timedelta(days=365)
    )

@pytest.mark.asyncio
async def test_register_serial(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    assert serial.serial_number == sample_serial_data.serial_number
    assert serial.status == SerialStatus.in_stock

    # Check history
    result = await db_session.execute(select(SerialHistory).where(SerialHistory.serial_id == serial.id))
    histories = list(result.scalars().all())
    assert len(histories) == 1
    assert histories[0].event_type.value == "received"

@pytest.mark.asyncio
async def test_update_status_valid(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    updated = await update_status(db_session, serial.id, SerialStatus.reserved.value, "ref", "123", None)
    assert updated.status == SerialStatus.reserved

    result = await db_session.execute(select(SerialHistory).where(SerialHistory.serial_id == serial.id))
    histories = list(result.scalars().all())
    assert len(histories) == 2

@pytest.mark.asyncio
async def test_update_status_invalid(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    with pytest.raises(BusinessRuleError):
        await update_status(db_session, serial.id, SerialStatus.shipped.value, "ref", "123", None)

@pytest.mark.asyncio
async def test_reserve(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    reserved_serial = await reserve(db_session, serial.id, "ref", "123")
    assert reserved_serial.status == SerialStatus.reserved

@pytest.mark.asyncio
async def test_ship(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    await reserve(db_session, serial.id, "ref", "123")
    shipped = await ship(db_session, serial.id, "CUST-1", date.today(), "sale", "S-1")
    assert shipped.status == SerialStatus.shipped
    assert shipped.customer_code == "CUST-1"

@pytest.mark.asyncio
async def test_return_serial(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    await reserve(db_session, serial.id, "ref", "123")
    await ship(db_session, serial.id, "CUST-1", date.today(), "sale", "S-1")
    returned = await return_serial(db_session, serial.id, "Defect", "ret", "R-1")
    assert returned.status == SerialStatus.in_stock
    assert returned.customer_code is None

@pytest.mark.asyncio
async def test_transfer(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    transferred = await transfer(db_session, serial.id, "WH-2", "BIN-1", "T-1")
    assert transferred.warehouse_code == "WH-2"
    assert transferred.bin_code == "BIN-1"

    result = await db_session.execute(select(SerialHistory).where(SerialHistory.serial_id == serial.id).order_by(SerialHistory.id.desc()))
    hist = result.scalars().first()
    assert hist.location_from == "WH-1"
    assert hist.location_to == "WH-2"

@pytest.mark.asyncio
async def test_scrap(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    scrapped = await scrap(db_session, serial.id, "Broken", "scrap", "SC-1")
    assert scrapped.status == SerialStatus.scrapped

@pytest.mark.asyncio
async def test_scrap_already_scrapped(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    await scrap(db_session, serial.id, "Broken", "scrap", "SC-1")
    with pytest.raises(BusinessRuleError):
        await scrap(db_session, serial.id, "Broken", "scrap", "SC-2")

@pytest.mark.asyncio
async def test_get_serial(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    found = await get_serial(db_session, serial.id)
    assert found.id == serial.id

@pytest.mark.asyncio
async def test_get_serial_not_found(db_session):
    with pytest.raises(NotFoundError):
        await get_serial(db_session, 999)

@pytest.mark.asyncio
async def test_trace_serial(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    req = SerialTraceRequest(serial_number=serial.serial_number, direction=TraceDirection.forward)
    trace = await trace_serial(db_session, req)
    assert trace.serial_number == serial.serial_number
    assert len(trace.history) == 1

@pytest.mark.asyncio
async def test_check_warranty(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)

    # Under warranty
    chk = WarrantyCheck(serial_number=serial.serial_number, check_date=date.today())
    res = await check_warranty(db_session, chk)
    assert res.is_under_warranty is True
    assert res.days_remaining == 365

    # Expired
    chk = WarrantyCheck(serial_number=serial.serial_number, check_date=date.today() + timedelta(days=400))
    res = await check_warranty(db_session, chk)
    assert res.is_under_warranty is False

@pytest.mark.asyncio
async def test_check_warranty_no_dates(db_session):
    data = SerialCreate(serial_number="SN-NO-WARRANTY", product_code="P1", warehouse_code="W1")
    serial = await register_serial(db_session, data)

    chk = WarrantyCheck(serial_number=serial.serial_number, check_date=date.today())
    res = await check_warranty(db_session, chk)
    assert res.is_under_warranty is False

@pytest.mark.asyncio
async def test_get_by_product(db_session, sample_serial_data):
    await register_serial(db_session, sample_serial_data)
    serials = await get_by_product(db_session, sample_serial_data.product_code)
    assert len(serials) == 1

@pytest.mark.asyncio
async def test_get_by_customer(db_session, sample_serial_data):
    serial = await register_serial(db_session, sample_serial_data)
    await reserve(db_session, serial.id, "ref", "123")
    await ship(db_session, serial.id, "CUST-X", date.today(), "sale", "S-1")

    serials = await get_by_customer(db_session, "CUST-X")
    assert len(serials) == 1

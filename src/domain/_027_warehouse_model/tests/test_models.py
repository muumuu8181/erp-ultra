import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain._027_warehouse_model.models import Warehouse, WarehouseZone, BinLocation
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

@pytest.mark.asyncio
async def test_warehouse_model(db: AsyncSession):
    w = Warehouse(code="WH01", name="Main WH", type="own")
    db.add(w)
    await db.commit()
    await db.refresh(w)
    assert w.id is not None
    assert w.code == "WH01"
    assert w.is_active is True

@pytest.mark.asyncio
async def test_warehouse_unique_code(db: AsyncSession):
    w1 = Warehouse(code="WH02", name="W1", type="own")
    w2 = Warehouse(code="WH02", name="W2", type="own")
    db.add(w1)
    await db.commit()
    db.add(w2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

@pytest.mark.asyncio
async def test_warehouse_zone_model(db: AsyncSession):
    w = Warehouse(code="WH03", name="WH3", type="own")
    db.add(w)
    await db.commit()

    z = WarehouseZone(warehouse_id=w.id, code="Z1", name="Zone 1", zone_type="storage")
    db.add(z)
    await db.commit()
    assert z.id is not None
    assert z.temperature_zone == "ambient"

@pytest.mark.asyncio
async def test_zone_unique_code_in_warehouse(db: AsyncSession):
    w = Warehouse(code="WH04", name="WH4", type="own")
    db.add(w)
    await db.commit()

    z1 = WarehouseZone(warehouse_id=w.id, code="Z1", name="Zone 1", zone_type="storage")
    z2 = WarehouseZone(warehouse_id=w.id, code="Z1", name="Zone 2", zone_type="storage")
    db.add(z1)
    await db.commit()

    db.add(z2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

@pytest.mark.asyncio
async def test_bin_model(db: AsyncSession):
    w = Warehouse(code="WH05", name="WH5", type="own")
    db.add(w)
    await db.commit()

    z = WarehouseZone(warehouse_id=w.id, code="Z1", name="Zone 1", zone_type="storage")
    db.add(z)
    await db.commit()

    b = BinLocation(zone_id=z.id, code="B1", name="Bin 1", capacity=Decimal("100.5"), current_usage=Decimal("10.0"))
    db.add(b)
    await db.commit()
    assert b.id is not None
    assert b.capacity == Decimal("100.5")

@pytest.mark.asyncio
async def test_bin_unique_code_in_zone(db: AsyncSession):
    w = Warehouse(code="WH06", name="WH6", type="own")
    db.add(w)
    await db.commit()

    z = WarehouseZone(warehouse_id=w.id, code="Z1", name="Zone 1", zone_type="storage")
    db.add(z)
    await db.commit()

    b1 = BinLocation(zone_id=z.id, code="B1", name="Bin 1")
    b2 = BinLocation(zone_id=z.id, code="B1", name="Bin 2")
    db.add(b1)
    await db.commit()

    db.add(b2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

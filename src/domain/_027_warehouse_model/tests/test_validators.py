import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain._027_warehouse_model.validators import (
    validate_warehouse_code_unique,
    validate_warehouse_exists,
    validate_zone_exists,
    validate_bin_code_unique_in_zone
)
from shared.errors import ValidationError, NotFoundError, DuplicateError
from src.domain._027_warehouse_model.models import Warehouse, WarehouseZone, BinLocation

def test_validate_warehouse_code_unique():
    assert validate_warehouse_code_unique("WH001") == "WH001"
    assert validate_warehouse_code_unique(" WH002 ") == "WH002"
    with pytest.raises(ValidationError):
        validate_warehouse_code_unique("")
    with pytest.raises(ValidationError):
        validate_warehouse_code_unique("   ")

@pytest.mark.asyncio
async def test_validate_warehouse_exists(db: AsyncSession):
    w = Warehouse(code="V_WH01", name="W", type="own")
    db.add(w)
    await db.commit()
    await db.refresh(w)

    await validate_warehouse_exists(db, w.id)

    with pytest.raises(NotFoundError):
        await validate_warehouse_exists(db, 99999)

@pytest.mark.asyncio
async def test_validate_zone_exists(db: AsyncSession):
    w = Warehouse(code="V_WH02", name="W", type="own")
    db.add(w)
    await db.commit()

    z = WarehouseZone(warehouse_id=w.id, code="V_Z01", name="Z", zone_type="storage")
    db.add(z)
    await db.commit()

    await validate_zone_exists(db, z.id)

    with pytest.raises(NotFoundError):
        await validate_zone_exists(db, 99999)

@pytest.mark.asyncio
async def test_validate_bin_code_unique_in_zone(db: AsyncSession):
    w = Warehouse(code="V_WH03", name="W", type="own")
    db.add(w)
    await db.commit()

    z = WarehouseZone(warehouse_id=w.id, code="V_Z01", name="Z", zone_type="storage")
    db.add(z)
    await db.commit()

    b = BinLocation(zone_id=z.id, code="V_B01", name="B")
    db.add(b)
    await db.commit()

    # Existing bin code -> raises
    with pytest.raises(DuplicateError):
        await validate_bin_code_unique_in_zone(db, z.id, "V_B01")

    # Same code but exclude id -> ok
    await validate_bin_code_unique_in_zone(db, z.id, "V_B01", exclude_id=b.id)

    # New code -> ok
    await validate_bin_code_unique_in_zone(db, z.id, "V_B02")

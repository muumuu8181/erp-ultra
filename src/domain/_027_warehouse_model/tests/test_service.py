import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain._027_warehouse_model import service
from src.domain._027_warehouse_model.schemas import (
    WarehouseCreate, WarehouseType, WarehouseUpdate,
    ZoneCreate, ZoneType,
    BinCreate
)
from shared.errors import DuplicateError, NotFoundError, ValidationError
from decimal import Decimal

@pytest.mark.asyncio
async def test_create_warehouse(db: AsyncSession):
    data = WarehouseCreate(code="S_WH01", name="S WH", type=WarehouseType.own)
    w = await service.create_warehouse(db, data)
    assert w.id is not None
    assert w.code == "S_WH01"

    with pytest.raises(DuplicateError):
        await service.create_warehouse(db, data)

@pytest.mark.asyncio
async def test_update_warehouse(db: AsyncSession):
    data = WarehouseCreate(code="S_WH02", name="S WH", type=WarehouseType.own)
    w = await service.create_warehouse(db, data)

    update_data = WarehouseUpdate(name="Updated WH")
    updated = await service.update_warehouse(db, w.id, update_data)
    assert updated.name == "Updated WH"
    assert updated.code == "S_WH02"

    with pytest.raises(NotFoundError):
        await service.update_warehouse(db, 9999, update_data)

@pytest.mark.asyncio
async def test_list_warehouses(db: AsyncSession):
    await service.create_warehouse(db, WarehouseCreate(code="S_WH03", name="WH3", type=WarehouseType.own))
    await service.create_warehouse(db, WarehouseCreate(code="S_WH04", name="WH4", type=WarehouseType.own))

    res = await service.list_warehouses(db, page=1, page_size=10)
    assert res.total >= 2

@pytest.mark.asyncio
async def test_create_zone(db: AsyncSession):
    w = await service.create_warehouse(db, WarehouseCreate(code="S_WH05", name="WH5", type=WarehouseType.own))

    data = ZoneCreate(code="S_Z01", name="Zone 1", zone_type=ZoneType.storage)
    z = await service.create_zone(db, w.id, data)
    assert z.id is not None

    with pytest.raises(NotFoundError):
        await service.create_zone(db, 9999, data)

    with pytest.raises(DuplicateError):
        await service.create_zone(db, w.id, data)

@pytest.mark.asyncio
async def test_list_zones(db: AsyncSession):
    w = await service.create_warehouse(db, WarehouseCreate(code="S_WH06", name="WH", type=WarehouseType.own))
    await service.create_zone(db, w.id, ZoneCreate(code="Z1", name="Z1", zone_type=ZoneType.storage))

    res = await service.list_zones(db, w.id, page=1, page_size=10)
    assert res.total == 1

@pytest.mark.asyncio
async def test_create_bin(db: AsyncSession):
    w = await service.create_warehouse(db, WarehouseCreate(code="S_WH07", name="WH", type=WarehouseType.own))
    z = await service.create_zone(db, w.id, ZoneCreate(code="Z1", name="Z1", zone_type=ZoneType.storage))

    data = BinCreate(code="B1", name="Bin 1", capacity=Decimal("100"), current_usage=Decimal("50"))
    b = await service.create_bin(db, z.id, data)
    assert b.id is not None

    with pytest.raises(NotFoundError):
        await service.create_bin(db, 9999, data)

    with pytest.raises(DuplicateError):
        await service.create_bin(db, z.id, data)

    data2 = BinCreate(code="B2", name="B2", capacity=Decimal("10"), current_usage=Decimal("20"))
    with pytest.raises(ValidationError):
        await service.create_bin(db, z.id, data2)

@pytest.mark.asyncio
async def test_list_bins(db: AsyncSession):
    w = await service.create_warehouse(db, WarehouseCreate(code="S_WH08", name="WH", type=WarehouseType.own))
    z = await service.create_zone(db, w.id, ZoneCreate(code="Z1", name="Z1", zone_type=ZoneType.storage))
    await service.create_bin(db, z.id, BinCreate(code="B1", name="B1"))

    res = await service.list_bins(db, z.id)
    assert res.total == 1

@pytest.mark.asyncio
async def test_get_warehouse_layout(db: AsyncSession):
    w = await service.create_warehouse(db, WarehouseCreate(code="S_WH09", name="WH", type=WarehouseType.own))
    z1 = await service.create_zone(db, w.id, ZoneCreate(code="Z1", name="Z1", zone_type=ZoneType.storage))
    await service.create_bin(db, z1.id, BinCreate(code="B1", name="B1"))

    layout = await service.get_warehouse_layout(db, w.id)
    assert layout.warehouse.code == "S_WH09"
    assert len(layout.zones) == 1
    assert layout.zones[0].code == "Z1"
    assert len(layout.zones[0].bins) == 1
    assert layout.zones[0].bins[0].code == "B1"

@pytest.mark.asyncio
async def test_deactivate_warehouse(db: AsyncSession):
    w = await service.create_warehouse(db, WarehouseCreate(code="S_WH10", name="WH", type=WarehouseType.own))
    z = await service.create_zone(db, w.id, ZoneCreate(code="Z1", name="Z1", zone_type=ZoneType.storage))
    b = await service.create_bin(db, z.id, BinCreate(code="B1", name="B1"))

    await service.deactivate_warehouse(db, w.id)

    # Checking DB directly using get or list
    w_deact = await service.list_warehouses(db, is_active=False)
    assert any(x.id == w.id for x in w_deact.items)

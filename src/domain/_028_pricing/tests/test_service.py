import pytest
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import DuplicateError, NotFoundError, ValidationError
from src.domain._028_pricing.schemas import (
    PriceListCreate, PriceListItemCreate, PriceLookupRequest
)
from src.domain._028_pricing import service
from src.domain._028_pricing.models import PriceList, PriceListItem

pytestmark = pytest.mark.asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from shared.types import Base

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(DATABASE_URL, echo=False, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

async def test_create_price_list(db_session: AsyncSession):
    data = PriceListCreate(name="Test", code="P1", valid_from=date(2023, 1, 1))
    pl = await service.create_price_list(db_session, data)
    assert pl.id is not None
    assert pl.code == "P1"

    with pytest.raises(DuplicateError):
        await service.create_price_list(db_session, data)

    with pytest.raises(ValidationError):
        bad_data = PriceListCreate(name="Test", code="P2", valid_from=date(2023, 1, 2), valid_to=date(2023, 1, 1))
        await service.create_price_list(db_session, bad_data)


async def test_update_price_list(db_session: AsyncSession):
    data = PriceListCreate(name="Original", code="P_UPD1", valid_from=date(2023, 1, 1))
    pl = await service.create_price_list(db_session, data)

    update_data = PriceListCreate(name="Updated", code="P_UPD1", valid_from=date(2023, 1, 1))
    updated_pl = await service.update_price_list(db_session, pl.id, update_data)
    assert updated_pl.name == "Updated"

    with pytest.raises(NotFoundError):
        await service.update_price_list(db_session, 999, update_data)


async def test_add_price_item(db_session: AsyncSession):
    pl_data = PriceListCreate(name="Test", code="P_ITEM1", valid_from=date(2023, 1, 1))
    pl = await service.create_price_list(db_session, pl_data)

    item_data = PriceListItemCreate(product_code="PROD-1", unit_price=Decimal("100"), min_quantity=Decimal("1"))
    item = await service.add_price_item(db_session, pl.id, item_data)

    assert item.id is not None
    assert item.product_code == "PROD-1"

    with pytest.raises(NotFoundError):
        await service.add_price_item(db_session, 999, item_data)


async def test_get_price(db_session: AsyncSession):
    pl_data = PriceListCreate(name="Test", code="P_GET1", valid_from=date(2023, 1, 1))
    pl = await service.create_price_list(db_session, pl_data)

    await service.add_price_item(db_session, pl.id, PriceListItemCreate(
        product_code="PROD-1", unit_price=Decimal("100"), min_quantity=Decimal("1")
    ))
    await service.add_price_item(db_session, pl.id, PriceListItemCreate(
        product_code="PROD-1", unit_price=Decimal("90"), min_quantity=Decimal("10")
    ))

    # Tier 1
    req1 = PriceLookupRequest(product_code="PROD-1", quantity=Decimal("5"), date=date(2023, 2, 1), price_list_id=None)
    resp1 = await service.get_price(db_session, req1)
    assert resp1.unit_price == Decimal("100")
    assert resp1.effective_price == Decimal("100")
    assert resp1.total_price == Decimal("500")

    # Tier 2
    req2 = PriceLookupRequest(product_code="PROD-1", quantity=Decimal("15"), date=date(2023, 2, 1), price_list_id=None)
    resp2 = await service.get_price(db_session, req2)
    assert resp2.unit_price == Decimal("90")
    assert resp2.effective_price == Decimal("90")
    assert resp2.total_price == Decimal("1350")

    # Specific list
    req3 = PriceLookupRequest(product_code="PROD-1", quantity=Decimal("5"), date=date(2023, 2, 1), price_list_id=pl.id)
    resp3 = await service.get_price(db_session, req3)
    assert resp3.unit_price == Decimal("100")


async def test_get_best_price(db_session: AsyncSession):
    pl1 = await service.create_price_list(db_session, PriceListCreate(name="List1", code="PB1", valid_from=date(2023, 1, 1)))
    pl2 = await service.create_price_list(db_session, PriceListCreate(name="List2", code="PB2", valid_from=date(2023, 1, 1)))

    await service.add_price_item(db_session, pl1.id, PriceListItemCreate(product_code="PROD-B", unit_price=Decimal("100"), min_quantity=Decimal("1")))
    await service.add_price_item(db_session, pl2.id, PriceListItemCreate(product_code="PROD-B", unit_price=Decimal("80"), min_quantity=Decimal("1")))

    req = PriceLookupRequest(product_code="PROD-B", quantity=Decimal("5"), date=date(2023, 2, 1), price_list_id=None)
    resp = await service.get_best_price(db_session, req)

    assert resp.price_list_id == pl2.id
    assert resp.unit_price == Decimal("80")


async def test_calculate_price(db_session: AsyncSession):
    pl = await service.create_price_list(db_session, PriceListCreate(name="ListC", code="PC1", valid_from=date(2023, 1, 1)))
    await service.add_price_item(db_session, pl.id, PriceListItemCreate(product_code="PROD-C", unit_price=Decimal("100"), min_quantity=Decimal("1")))

    resp = await service.calculate_price(db_session, "PROD-C", Decimal("5"), date(2023, 2, 1))
    assert resp.total_price == Decimal("500")


async def test_list_price_lists(db_session: AsyncSession):
    await service.create_price_list(db_session, PriceListCreate(name="L1", code="PLIST_1", valid_from=date(2023, 1, 1), is_active=True))
    await service.create_price_list(db_session, PriceListCreate(name="L2", code="PLIST_2", valid_from=date(2023, 1, 1), is_active=False))

    resp = await service.list_price_lists(db_session)
    assert len(resp.items) >= 2

    resp_active = await service.list_price_lists(db_session, is_active=True)
    assert all(item.is_active for item in resp_active.items)


async def test_duplicate_price_list(db_session: AsyncSession):
    pl = await service.create_price_list(db_session, PriceListCreate(name="Source", code="PDUP_S", valid_from=date(2023, 1, 1)))
    await service.add_price_item(db_session, pl.id, PriceListItemCreate(product_code="PROD-D", unit_price=Decimal("100"), min_quantity=Decimal("1")))

    new_pl = await service.duplicate_price_list(db_session, pl.id, "PDUP_T", "Target")

    assert new_pl.id != pl.id
    assert new_pl.code == "PDUP_T"
    assert new_pl.name == "Target"
    assert new_pl.is_active is False

    result = await db_session.execute(select(PriceListItem).where(PriceListItem.price_list_id == new_pl.id))
    items = result.scalars().all()
    assert len(items) == 1
    assert items[0].product_code == "PROD-D"

    with pytest.raises(DuplicateError):
        await service.duplicate_price_list(db_session, pl.id, "PDUP_T")

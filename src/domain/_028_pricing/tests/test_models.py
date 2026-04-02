import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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

async def test_pricelist_instantiation_defaults(db_session: AsyncSession):
    pl = PriceList(
        name="Test List",
        code="TEST-001",
        valid_from=date(2023, 1, 1)
    )
    db_session.add(pl)
    await db_session.commit()
    await db_session.refresh(pl)

    assert pl.id is not None
    assert pl.name == "Test List"
    assert pl.code == "TEST-001"
    assert pl.valid_from == date(2023, 1, 1)
    assert pl.valid_to is None
    assert pl.currency_code == 'JPY'
    assert pl.is_active is True

async def test_pricelist_unique_constraint(db_session: AsyncSession):
    pl1 = PriceList(name="List 1", code="UNIQUE", valid_from=date(2023, 1, 1))
    db_session.add(pl1)
    await db_session.commit()

    pl2 = PriceList(name="List 2", code="UNIQUE", valid_from=date(2023, 1, 1))
    db_session.add(pl2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

async def test_pricelistitem_instantiation(db_session: AsyncSession):
    pl = PriceList(name="Test List", code="ITEM-TEST", valid_from=date(2023, 1, 1))
    db_session.add(pl)
    await db_session.flush()

    item = PriceListItem(
        price_list_id=pl.id,
        product_code="PROD-1",
        unit_price=Decimal("100.50"),
        discount_percentage=Decimal("5.00"),
        min_quantity=Decimal("10.000")
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    assert item.id is not None
    assert item.price_list_id == pl.id
    assert item.product_code == "PROD-1"
    assert item.unit_price == Decimal("100.50")
    assert item.discount_percentage == Decimal("5.00")
    assert item.min_quantity == Decimal("10.000")

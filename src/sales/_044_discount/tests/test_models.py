import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.sales._044_discount.models import DiscountRule, DiscountUsage, DiscountType, AppliesTo
from shared.types import Base

# Setup a test DB fixture
@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db(engine):
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()

@pytest.mark.asyncio
async def test_discount_rule_creation(db: AsyncSession):
    rule = DiscountRule(
        name="Test Rule",
        code="TEST01",
        discount_type=DiscountType.percentage,
        value=Decimal("10.00"),
        applies_to=AppliesTo.order_total,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        is_stackable=True,
        is_active=True
    )
    db.add(rule)
    await db.flush()
    assert rule.id is not None
    assert rule.current_uses == 0

@pytest.mark.asyncio
async def test_discount_usage_creation(db: AsyncSession):
    rule = DiscountRule(
        name="Test Rule 2",
        code="TEST02",
        discount_type=DiscountType.fixed_amount,
        value=Decimal("50.00"),
        applies_to=AppliesTo.order_total,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        is_stackable=True,
        is_active=True
    )
    db.add(rule)
    await db.flush()

    usage = DiscountUsage(
        rule_id=rule.id,
        order_number="ORD-001",
        customer_code="CUST-001",
        discount_amount=Decimal("50.00"),
        used_at=datetime.now()
    )
    db.add(usage)
    await db.flush()
    assert usage.id is not None

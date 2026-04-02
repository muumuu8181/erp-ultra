import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.sales._044_discount import service
from src.sales._044_discount.schemas import DiscountRuleCreate, DiscountApplyRequest, OrderLine
from src.sales._044_discount.models import DiscountType, AppliesTo, DiscountRule
from shared.types import Base
from shared.errors import NotFoundError, DuplicateError, BusinessRuleError, ValidationError

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
async def test_create_rule(db: AsyncSession):
    data = DiscountRuleCreate(
        name="Test",
        code="CODE1",
        discount_type=DiscountType.fixed_amount,
        value=Decimal("100"),
        applies_to=AppliesTo.order_total,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        is_stackable=True,
        is_active=True
    )
    rule = await service.create_rule(db, data)
    assert rule.id is not None
    assert rule.code == "CODE1"

@pytest.mark.asyncio
async def test_create_rule_duplicate(db: AsyncSession):
    data = DiscountRuleCreate(
        name="Test",
        code="CODE1",
        discount_type=DiscountType.fixed_amount,
        value=Decimal("100"),
        applies_to=AppliesTo.order_total,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        is_stackable=True,
        is_active=True
    )
    await service.create_rule(db, data)
    with pytest.raises(DuplicateError):
        await service.create_rule(db, data)

@pytest.mark.asyncio
async def test_apply_discount(db: AsyncSession):
    rule = DiscountRule(
        name="10% Off",
        code="TENOFF",
        discount_type=DiscountType.percentage,
        value=Decimal("10.0"),
        applies_to=AppliesTo.order_total,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today() + timedelta(days=10),
        is_stackable=True,
        is_active=True
    )
    db.add(rule)
    await db.flush()

    req = DiscountApplyRequest(
        order_lines=[OrderLine(product_code="P1", quantity=Decimal("1"), unit_price=Decimal("100"))],
        customer_code="C1",
        order_total=Decimal("100")
    )

    resp = await service.apply_discount(db, req)
    assert resp.total_discount == Decimal("10.0")
    assert resp.final_total == Decimal("90.0")
    assert len(resp.applied_discounts) == 1
    assert rule.current_uses == 1

@pytest.mark.asyncio
async def test_apply_discount_stacking(db: AsyncSession):
    # Rule 1: Stackable 10% off
    rule1 = DiscountRule(
        name="10% Off",
        code="TENOFF",
        discount_type=DiscountType.percentage,
        value=Decimal("10.0"),
        applies_to=AppliesTo.order_total,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today() + timedelta(days=10),
        is_stackable=True,
        is_active=True
    )
    # Rule 2: Stackable $5 off
    rule2 = DiscountRule(
        name="5 Off",
        code="FIVEOFF",
        discount_type=DiscountType.fixed_amount,
        value=Decimal("5.0"),
        applies_to=AppliesTo.order_total,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today() + timedelta(days=10),
        is_stackable=True,
        is_active=True
    )
    # Rule 3: Non-stackable $20 off
    rule3 = DiscountRule(
        name="20 Off",
        code="TWENTYOFF",
        discount_type=DiscountType.fixed_amount,
        value=Decimal("20.0"),
        applies_to=AppliesTo.order_total,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today() + timedelta(days=10),
        is_stackable=False,
        is_active=True
    )
    db.add_all([rule1, rule2, rule3])
    await db.flush()

    req = DiscountApplyRequest(
        order_lines=[OrderLine(product_code="P1", quantity=Decimal("1"), unit_price=Decimal("100"))],
        customer_code="C1",
        order_total=Decimal("100")
    )

    resp = await service.apply_discount(db, req)
    # Combined stackable = $10 + $5 = $15
    # Best non-stackable = $20
    # Should choose rule 3 ($20)
    assert resp.total_discount == Decimal("20.0")
    assert len(resp.applied_discounts) == 1
    assert resp.applied_discounts[0].code == "TWENTYOFF"

@pytest.mark.asyncio
async def test_validate_discount_limit(db: AsyncSession):
    rule = DiscountRule(
        name="Limit",
        code="LIMIT",
        discount_type=DiscountType.fixed_amount,
        value=Decimal("10.0"),
        applies_to=AppliesTo.order_total,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today() + timedelta(days=10),
        is_stackable=True,
        is_active=True,
        max_uses=1,
        current_uses=1
    )
    db.add(rule)
    await db.flush()

    with pytest.raises(BusinessRuleError):
        await service.validate_discount(db, "LIMIT", "C1", Decimal("100"))

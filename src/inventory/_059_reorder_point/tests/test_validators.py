import pytest
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError, DuplicateError, CalculationError
from src.inventory._059_reorder_point.models import ReorderPoint
from src.inventory._059_reorder_point.schemas import ReviewCycleEnum
from src.inventory._059_reorder_point.validators import (
    validate_reorder_point_logic,
    validate_reorder_quantity,
    validate_lead_time_days,
    validate_unique_product_warehouse,
    calculate_safety_stock_formula,
    calculate_eoq_formula
)

pytestmark = pytest.mark.asyncio


async def test_validate_reorder_point_logic():
    # Should pass
    await validate_reorder_point_logic(Decimal("100"), Decimal("50"))
    await validate_reorder_point_logic(Decimal("50"), Decimal("50"))

    # Should fail
    with pytest.raises(ValidationError):
        await validate_reorder_point_logic(Decimal("40"), Decimal("50"))


async def test_validate_reorder_quantity():
    # Should pass
    await validate_reorder_quantity(Decimal("10"))

    # Should fail
    with pytest.raises(ValidationError):
        await validate_reorder_quantity(Decimal("0"))
    with pytest.raises(ValidationError):
        await validate_reorder_quantity(Decimal("-5"))


async def test_validate_lead_time_days():
    # Should pass
    await validate_lead_time_days(1)
    await validate_lead_time_days(10)

    # Should fail
    with pytest.raises(ValidationError):
        await validate_lead_time_days(0)
    with pytest.raises(ValidationError):
        await validate_lead_time_days(-1)


async def test_validate_unique_product_warehouse(db: AsyncSession):
    # Setup initial record
    rp = ReorderPoint(
        product_code="PROD-VAL-1",
        warehouse_code="WH-VAL-A",
        reorder_point=Decimal("100"),
        safety_stock=Decimal("20"),
        reorder_quantity=Decimal("50"),
        lead_time_days=7,
        review_cycle=ReviewCycleEnum.DAILY.value,
    )
    db.add(rp)
    await db.flush()

    # Should pass for different product/warehouse
    await validate_unique_product_warehouse(db, "PROD-VAL-2", "WH-VAL-A")
    await validate_unique_product_warehouse(db, "PROD-VAL-1", "WH-VAL-B")

    # Should pass if excluding self
    await validate_unique_product_warehouse(db, "PROD-VAL-1", "WH-VAL-A", exclude_id=rp.id)

    # Should fail for exact duplicate
    with pytest.raises(DuplicateError):
        await validate_unique_product_warehouse(db, "PROD-VAL-1", "WH-VAL-A")


def test_calculate_safety_stock_formula():
    # Test known inputs: Z=1.65, sigma=10, LT=7
    # sqrt(7) ~= 2.64575
    # 1.65 * 10 * 2.64575 = 43.6548... -> 43.655
    res = calculate_safety_stock_formula(Decimal("10"), 7, Decimal("1.65"))
    assert res == Decimal("43.655")

    # Zero sigma
    res_zero = calculate_safety_stock_formula(Decimal("0"), 7, Decimal("1.65"))
    assert res_zero == Decimal("0.000")

    # Error for negative values
    with pytest.raises(CalculationError):
        calculate_safety_stock_formula(Decimal("-10"), 7, Decimal("1.65"))


def test_calculate_eoq_formula():
    # Test with just holding_cost_pct as total holding cost
    # D=1000, S=10, H=2
    # EOQ = sqrt(2 * 1000 * 10 / 2) = sqrt(10000) = 100
    res = calculate_eoq_formula(Decimal("1000"), Decimal("10"), Decimal("2"))
    assert res == Decimal("100.000")

    # Test with unit cost
    # H = 0.2 * 10 = 2
    res2 = calculate_eoq_formula(Decimal("1000"), Decimal("10"), Decimal("0.2"), Decimal("10"))
    assert res2 == Decimal("100.000")

    # Error cases
    with pytest.raises(CalculationError):
        calculate_eoq_formula(Decimal("0"), Decimal("10"), Decimal("2"))

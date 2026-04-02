import pytest
from datetime import date
from decimal import Decimal
import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, ValidationError, CalculationError
from src.inventory._061_inventory_valuation.validators import (
    validate_one_method_per_product,
    validate_positive_unit_cost,
    validate_method_enum,
    consume_fifo,
    consume_lifo,
    calculate_weighted_average
)
from src.inventory._061_inventory_valuation.models import ValuationMethod, CostLayer

pytestmark = pytest.mark.asyncio

async def test_validate_one_method_per_product(db_session):
    method = ValuationMethod(
        product_code="TEST-VAL",
        method="fifo",
        effective_from=date.today(),
        is_active=True
    )
    db_session.add(method)
    await db_session.flush()

    with pytest.raises(DuplicateError):
        await validate_one_method_per_product(db_session, "TEST-VAL")

def test_validate_positive_unit_cost():
    with pytest.raises(ValidationError):
        validate_positive_unit_cost(Decimal('0'))
    with pytest.raises(ValidationError):
        validate_positive_unit_cost(Decimal('-10'))

    validate_positive_unit_cost(Decimal('10')) # Should not raise

def test_validate_method_enum():
    with pytest.raises(ValidationError):
        validate_method_enum("invalid_method")

    validate_method_enum("fifo") # Should not raise

def test_consume_fifo():
    layer1 = CostLayer(received_date=datetime.date(2023, 1, 1), layer_number=1, remaining_quantity=Decimal('10'))
    layer2 = CostLayer(received_date=datetime.date(2023, 1, 2), layer_number=2, remaining_quantity=Decimal('20'))
    layers = [layer1, layer2]

    consumed = consume_fifo(layers, Decimal('15'))

    assert len(consumed) == 2
    assert layer1.remaining_quantity == Decimal('0')
    assert layer2.remaining_quantity == Decimal('15')

def test_consume_lifo():
    # LIFO layers are provided newest first by the service
    layer2 = CostLayer(received_date=datetime.date(2023, 1, 2), layer_number=2, remaining_quantity=Decimal('20'))
    layer1 = CostLayer(received_date=datetime.date(2023, 1, 1), layer_number=1, remaining_quantity=Decimal('10'))
    layers = [layer2, layer1]

    consumed = consume_lifo(layers, Decimal('15'))

    assert len(consumed) == 1
    assert layer2.remaining_quantity == Decimal('5')
    assert layer1.remaining_quantity == Decimal('10')

def test_consume_not_enough_inventory():
    layer1 = CostLayer(received_date=datetime.date(2023, 1, 1), layer_number=1, remaining_quantity=Decimal('10'))
    with pytest.raises(CalculationError):
        consume_fifo([layer1], Decimal('20'))

def test_calculate_weighted_average():
    layer1 = CostLayer(remaining_quantity=Decimal('10'), unit_cost=Decimal('10'))
    layer2 = CostLayer(remaining_quantity=Decimal('10'), unit_cost=Decimal('20'))

    avg = calculate_weighted_average([layer1, layer2])
    assert avg == Decimal('15') # (100 + 200) / 20 = 15

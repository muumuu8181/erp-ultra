"""
Tests for Unit of Measure models.
"""
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from src.domain._026_unit_of_measure.models import UnitOfMeasure, UomConversion
from src.domain._026_unit_of_measure.schemas import UomType


@pytest.mark.asyncio
async def test_uom_instantiation(db_session):
    uom = UnitOfMeasure(
        code="TEST",
        name="Test Unit",
        symbol="tst",
        uom_type=UomType.count.value
    )
    db_session.add(uom)
    await db_session.commit()
    await db_session.refresh(uom)

    assert uom.id is not None
    assert uom.code == "TEST"
    assert uom.decimal_places == 0
    assert uom.is_active is True
    assert uom.created_at is not None
    assert uom.updated_at is not None


@pytest.mark.asyncio
async def test_uom_code_unique(db_session):
    uom1 = UnitOfMeasure(
        code="DUP",
        name="Unit 1",
        symbol="u1",
        uom_type=UomType.count.value
    )
    db_session.add(uom1)
    await db_session.commit()

    uom2 = UnitOfMeasure(
        code="DUP",
        name="Unit 2",
        symbol="u2",
        uom_type=UomType.weight.value
    )
    db_session.add(uom2)
    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_uom_conversion_instantiation(db_session):
    uom1 = UnitOfMeasure(code="U1", name="Unit 1", symbol="u1", uom_type="count")
    uom2 = UnitOfMeasure(code="U2", name="Unit 2", symbol="u2", uom_type="count")
    db_session.add_all([uom1, uom2])
    await db_session.commit()
    await db_session.refresh(uom1)
    await db_session.refresh(uom2)

    conv = UomConversion(
        from_uom_id=uom1.id,
        to_uom_id=uom2.id,
        factor=Decimal("10.5")
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    assert conv.id is not None
    assert conv.from_uom_id == uom1.id
    assert conv.to_uom_id == uom2.id
    assert conv.factor == Decimal("10.5")
    assert conv.is_standard is False


@pytest.mark.asyncio
async def test_uom_conversion_unique_pair(db_session):
    uom1 = UnitOfMeasure(code="U3", name="Unit 3", symbol="u3", uom_type="count")
    uom2 = UnitOfMeasure(code="U4", name="Unit 4", symbol="u4", uom_type="count")
    db_session.add_all([uom1, uom2])
    await db_session.commit()

    conv1 = UomConversion(from_uom_id=uom1.id, to_uom_id=uom2.id, factor=Decimal("2"))
    db_session.add(conv1)
    await db_session.commit()

    conv2 = UomConversion(from_uom_id=uom1.id, to_uom_id=uom2.id, factor=Decimal("3"))
    db_session.add(conv2)
    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()

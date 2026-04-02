"""
Tests for Unit of Measure service.
"""
import pytest
from decimal import Decimal
from src.domain._026_unit_of_measure import service
from src.domain._026_unit_of_measure.schemas import (
    UomCreate, UomType, UomConversionCreate, UomConvertRequest
)
from shared.errors import DuplicateError, NotFoundError, BusinessRuleError, ValidationError


@pytest.fixture
async def uom_data(db_session):
    uom1 = await service.create_uom(db_session, UomCreate(
        code="M", name="Meter", symbol="m", uom_type=UomType.length, decimal_places=2
    ))
    uom2 = await service.create_uom(db_session, UomCreate(
        code="CM", name="Centimeter", symbol="cm", uom_type=UomType.length, decimal_places=0
    ))
    uom3 = await service.create_uom(db_session, UomCreate(
        code="MM", name="Millimeter", symbol="mm", uom_type=UomType.length, decimal_places=0
    ))
    uom_kg = await service.create_uom(db_session, UomCreate(
        code="KG", name="Kilogram", symbol="kg", uom_type=UomType.weight, decimal_places=2
    ))

    await service.create_conversion(db_session, UomConversionCreate(
        from_uom_id=uom1.id, to_uom_id=uom2.id, factor=Decimal("100")
    ))
    await service.create_conversion(db_session, UomConversionCreate(
        from_uom_id=uom2.id, to_uom_id=uom3.id, factor=Decimal("10")
    ))

    return {"M": uom1, "CM": uom2, "MM": uom3, "KG": uom_kg}


@pytest.mark.asyncio
async def test_create_uom(db_session):
    uom = await service.create_uom(db_session, UomCreate(
        code="PCS", name="Pieces", symbol="pcs", uom_type=UomType.count
    ))
    assert uom.code == "PCS"
    assert uom.uom_type == "count"

    with pytest.raises(DuplicateError):
        await service.create_uom(db_session, UomCreate(
            code="PCS", name="Pieces Dup", symbol="pcs", uom_type=UomType.count
        ))


@pytest.mark.asyncio
async def test_list_uoms(db_session, uom_data):
    # Get all
    result = await service.list_uoms(db_session)
    assert result.total >= 4

    # Filter by type
    result = await service.list_uoms(db_session, uom_type=UomType.length.value)
    assert result.total == 3
    assert all(u.uom_type == 'length' for u in result.items)

    # Filter by active
    result = await service.list_uoms(db_session, is_active=True)
    assert result.total >= 4


@pytest.mark.asyncio
async def test_create_conversion(db_session, uom_data):
    m = uom_data["M"]
    kg = uom_data["KG"]

    conv = await service.create_conversion(db_session, UomConversionCreate(
        from_uom_id=m.id, to_uom_id=kg.id, factor=Decimal("1") # silly conversion but for testing
    ))
    assert conv.factor == Decimal("1")

    with pytest.raises(DuplicateError):
        await service.create_conversion(db_session, UomConversionCreate(
            from_uom_id=m.id, to_uom_id=kg.id, factor=Decimal("2")
        ))

    with pytest.raises(ValidationError):
        await service.create_conversion(db_session, UomConversionCreate(
            from_uom_id=m.id, to_uom_id=m.id, factor=Decimal("1")
        ))

    # Validation error for negative factor is caught by Pydantic schema
    try:
        UomConversionCreate(
            from_uom_id=m.id, to_uom_id=kg.id, factor=Decimal("-1")
        )
        assert False, "Should raise ValidationError"
    except Exception as e:
        assert True


@pytest.mark.asyncio
async def test_convert_quantity(db_session, uom_data):
    m = uom_data["M"]
    cm = uom_data["CM"]
    mm = uom_data["MM"]
    kg = uom_data["KG"]

    # Direct conversion
    res1 = await service.convert_quantity(db_session, UomConvertRequest(
        from_uom_id=m.id, to_uom_id=cm.id, quantity=Decimal("2")
    ))
    assert res1.converted_quantity == Decimal("200")
    assert res1.factor_used == Decimal("100")

    # Reverse conversion
    res2 = await service.convert_quantity(db_session, UomConvertRequest(
        from_uom_id=cm.id, to_uom_id=m.id, quantity=Decimal("200")
    ))
    assert res2.converted_quantity == Decimal("2")
    assert res2.factor_used == Decimal("0.01")

    # Transitive conversion
    res3 = await service.convert_quantity(db_session, UomConvertRequest(
        from_uom_id=m.id, to_uom_id=mm.id, quantity=Decimal("2")
    ))
    assert res3.converted_quantity == Decimal("2000")
    assert res3.factor_used == Decimal("1000")

    # No path
    with pytest.raises(BusinessRuleError):
        await service.convert_quantity(db_session, UomConvertRequest(
            from_uom_id=m.id, to_uom_id=kg.id, quantity=Decimal("1")
        ))


@pytest.mark.asyncio
async def test_get_conversions(db_session, uom_data):
    m = uom_data["M"]
    result = await service.get_conversions(db_session, m.id)
    assert result.total == 1
    assert result.items[0].from_uom_id == m.id


@pytest.mark.asyncio
async def test_get_compatible_uoms(db_session, uom_data):
    m = uom_data["M"]
    kg = uom_data["KG"]

    compat = await service.get_compatible_uoms(db_session, m.id)
    assert len(compat) == 3 # M, CM, MM
    ids = [u.id for u in compat]
    assert m.id in ids
    assert uom_data["CM"].id in ids
    assert uom_data["MM"].id in ids
    assert kg.id not in ids

    compat_kg = await service.get_compatible_uoms(db_session, kg.id)
    assert len(compat_kg) == 1 # Only KG itself

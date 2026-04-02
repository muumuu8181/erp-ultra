import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from shared.errors import ValidationError, NotFoundError
from src.domain._017_product_model.validators import (
    validate_product_code,
    validate_positive_price,
    validate_unit,
    validate_category_exists
)

def test_validate_product_code_valid():
    validate_product_code("PRD-00001")
    validate_product_code("PRD-ABC12")

def test_validate_product_code_invalid():
    with pytest.raises(ValidationError):
        validate_product_code("PRD-")

    with pytest.raises(ValidationError):
        validate_product_code("XXX-12345")

    with pytest.raises(ValidationError):
        validate_product_code("prd-12345")

def test_validate_positive_price_valid():
    validate_positive_price(Decimal("0.0"), "price")
    validate_positive_price(Decimal("100.50"), "price")

def test_validate_positive_price_invalid():
    with pytest.raises(ValidationError):
        validate_positive_price(Decimal("-10.0"), "price")

def test_validate_unit_valid():
    for unit in ["pcs", "kg", "m", "l", "box", "set", "pair", "roll", "sheet"]:
        validate_unit(unit)

def test_validate_unit_invalid():
    with pytest.raises(ValidationError):
        validate_unit("invalid_unit")

@pytest.mark.asyncio
async def test_validate_category_exists_found():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = MagicMock()
    mock_db.execute.return_value = mock_result

    await validate_category_exists(mock_db, "Electronics")
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_validate_category_exists_not_found():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(NotFoundError):
        await validate_category_exists(mock_db, "NonExistent")

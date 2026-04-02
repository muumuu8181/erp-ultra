import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from shared.errors import DuplicateError, NotFoundError, ValidationError
from src.domain._017_product_model.service import (
    create_product, update_product, get_product, list_products, deactivate_product,
    create_category, list_categories, search_products, update_pricing
)
from src.domain._017_product_model.schemas import (
    ProductCreate, ProductUpdate, ProductCategoryCreate, ProductSearchFilter
)

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.mark.asyncio
async def test_create_product_success(mock_db):
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db.execute.return_value = mock_result

    data = ProductCreate(
        code="PRD-00001",
        name="Test",
        unit="pcs",
        standard_price=Decimal("10.0"),
        cost_price=Decimal("5.0"),
        tax_type="standard_10"
    )

    product = await create_product(mock_db, data)
    assert product.code == "PRD-00001"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_product_duplicate_code(mock_db):
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = MagicMock()
    mock_db.execute.return_value = mock_result

    data = ProductCreate(
        code="PRD-00001",
        name="Test",
        unit="pcs",
        standard_price=Decimal("10.0"),
        cost_price=Decimal("5.0"),
        tax_type="standard_10"
    )

    with pytest.raises(DuplicateError):
        await create_product(mock_db, data)

@pytest.mark.asyncio
async def test_update_product_success(mock_db):
    mock_product = MagicMock()
    mock_product.barcode = "123"

    mock_result = MagicMock()
    mock_result.scalars().first.side_effect = [mock_product, None] # First for get_product, second for barcode check
    mock_db.execute.return_value = mock_result

    data = ProductUpdate(name="New Name")

    product = await update_product(mock_db, 1, data)
    assert product.name == "New Name"
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_product_not_found(mock_db):
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db.execute.return_value = mock_result

    data = ProductUpdate(name="New Name")

    with pytest.raises(NotFoundError):
        await update_product(mock_db, 1, data)

@pytest.mark.asyncio
async def test_get_product_success(mock_db):
    mock_result = MagicMock()
    mock_product = MagicMock()
    mock_result.scalars().first.return_value = mock_product
    mock_db.execute.return_value = mock_result

    product = await get_product(mock_db, 1)
    assert product == mock_product

@pytest.mark.asyncio
async def test_get_product_not_found(mock_db):
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(NotFoundError):
        await get_product(mock_db, 1)

@pytest.mark.asyncio
async def test_list_products(mock_db):
    mock_db.scalar.return_value = 2

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [MagicMock(), MagicMock()]
    mock_db.execute.return_value = mock_result

    res = await list_products(mock_db, page=1, page_size=10)
    assert res.total == 2
    assert len(res.items) == 2

@pytest.mark.asyncio
async def test_deactivate_product(mock_db):
    mock_result = MagicMock()
    mock_product = MagicMock()
    mock_result.scalars().first.return_value = mock_product
    mock_db.execute.return_value = mock_result

    product = await deactivate_product(mock_db, 1)
    assert product.is_active is False
    assert product.is_deleted is True
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_category_success(mock_db):
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db.execute.return_value = mock_result

    data = ProductCategoryCreate(name="Tech")

    cat = await create_category(mock_db, data)
    assert cat.name == "Tech"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_category_duplicate(mock_db):
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = MagicMock()
    mock_db.execute.return_value = mock_result

    data = ProductCategoryCreate(name="Tech")

    with pytest.raises(DuplicateError):
        await create_category(mock_db, data)

@pytest.mark.asyncio
async def test_create_category_invalid_parent(mock_db):
    mock_result = MagicMock()
    mock_result.scalars().first.side_effect = [None, None] # None for name check, None for parent check
    mock_db.execute.return_value = mock_result

    data = ProductCategoryCreate(name="Tech", parent_id=99)

    with pytest.raises(NotFoundError):
        await create_category(mock_db, data)

@pytest.mark.asyncio
async def test_list_categories(mock_db):
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [MagicMock()]
    mock_db.execute.return_value = mock_result

    cats = await list_categories(mock_db)
    assert len(cats) == 1

@pytest.mark.asyncio
async def test_search_products(mock_db):
    mock_db.scalar.return_value = 1

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [MagicMock()]
    mock_db.execute.return_value = mock_result

    filters = ProductSearchFilter(query="Test", min_price=Decimal("10.0"))

    res = await search_products(mock_db, filters)
    assert res.total == 1
    assert len(res.items) == 1

@pytest.mark.asyncio
async def test_update_pricing_success(mock_db):
    mock_result = MagicMock()
    mock_product = MagicMock()
    mock_result.scalars().first.return_value = mock_product
    mock_db.execute.return_value = mock_result

    product = await update_pricing(mock_db, 1, standard_price=Decimal("15.0"))
    assert product.standard_price == Decimal("15.0")
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_pricing_negative(mock_db):
    mock_result = MagicMock()
    mock_product = MagicMock()
    mock_result.scalars().first.return_value = mock_product
    mock_db.execute.return_value = mock_result

    with pytest.raises(ValidationError):
        await update_pricing(mock_db, 1, standard_price=Decimal("-15.0"))

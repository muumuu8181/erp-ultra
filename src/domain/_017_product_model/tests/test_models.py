import pytest
from decimal import Decimal
from src.domain._017_product_model.models import Product, ProductCategory

def test_product_model_creation():
    product = Product(
        code="PRD-00001",
        name="Test Product",
        unit="pcs",
        standard_price=Decimal("100.00"),
        cost_price=Decimal("50.00"),
        tax_type="standard_10",
        barcode="123456789"
    )

    assert product.code == "PRD-00001"
    assert product.name == "Test Product"
    assert product.unit == "pcs"
    assert product.standard_price == Decimal("100.00")
    assert product.cost_price == Decimal("50.00")
    assert product.tax_type == "standard_10"

    # Defaults handled by DB/Schema mostly, but for instantiated models:
    pass

def test_product_category_model_creation():
    parent_category = ProductCategory(
        name="Electronics",
        sort_order=1
    )

    child_category = ProductCategory(
        name="Laptops",
        parent_id=1,
        sort_order=2
    )

    assert parent_category.name == "Electronics"
    assert parent_category.sort_order == 1

    assert child_category.name == "Laptops"
    assert child_category.parent_id == 1

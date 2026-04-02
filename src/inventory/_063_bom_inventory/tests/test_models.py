import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.inventory._063_bom_inventory.models import BOM, BOMItem

@pytest.mark.asyncio
async def test_bom_creation():
    bom = BOM(product_id="PROD-001", quantity=10, status="active", version=1)

    assert bom.product_id == "PROD-001"
    assert bom.quantity == 10
    assert bom.status == "active"
    assert bom.version == 1

@pytest.mark.asyncio
async def test_bom_item_creation():
    bom = BOM(id=1, product_id="PROD-001")
    item = BOMItem(bom_id=1, component_id="COMP-001", quantity_required=2, uom="pcs")

    assert item.bom_id == 1
    assert item.component_id == "COMP-001"
    assert item.quantity_required == 2
    assert item.uom == "pcs"

    item.bom = bom
    assert item.bom.product_id == "PROD-001"

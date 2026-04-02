import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from shared.types import Base
from src.inventory._063_bom_inventory.models import BOM, BOMItem
from src.inventory._063_bom_inventory.schemas import BOMCreate, BOMItemCreate
from src.inventory._063_bom_inventory.service import (
    create_bom,
    get_bom,
    list_boms,
    update_bom,
    delete_bom,
    add_bom_item,
    remove_bom_item
)
from shared.errors import NotFoundError, ValidationError, BusinessRuleError

# Setup test DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_bom(db: AsyncSession):
    bom_in = BOMCreate(product_id="P-01", quantity=1)
    bom = await create_bom(db, bom_in)

    assert bom.id is not None
    assert bom.product_id == "P-01"
    assert bom.quantity == 1


from pydantic import ValidationError as PydanticValidationError

@pytest.mark.asyncio
async def test_create_bom_invalid_quantity(db: AsyncSession):
    with pytest.raises(PydanticValidationError):
        bom_in = BOMCreate(product_id="P-01", quantity=0)
        await create_bom(db, bom_in)


@pytest.mark.asyncio
async def test_get_bom(db: AsyncSession):
    bom_in = BOMCreate(product_id="P-01", quantity=1)
    bom = await create_bom(db, bom_in)

    fetched = await get_bom(db, bom.id)
    assert fetched.id == bom.id
    assert fetched.product_id == "P-01"


@pytest.mark.asyncio
async def test_get_bom_not_found(db: AsyncSession):
    with pytest.raises(NotFoundError):
        await get_bom(db, 999)


@pytest.mark.asyncio
async def test_list_boms(db: AsyncSession):
    await create_bom(db, BOMCreate(product_id="P-01"))
    await create_bom(db, BOMCreate(product_id="P-02"))

    boms = await list_boms(db)
    assert len(boms) == 2


@pytest.mark.asyncio
async def test_update_bom(db: AsyncSession):
    bom = await create_bom(db, BOMCreate(product_id="P-01", quantity=1))

    updated = await update_bom(db, bom.id, BOMCreate(product_id="P-02", quantity=2))
    assert updated.product_id == "P-02"
    assert updated.quantity == 2


@pytest.mark.asyncio
async def test_delete_bom(db: AsyncSession):
    bom = await create_bom(db, BOMCreate(product_id="P-01"))

    await delete_bom(db, bom.id)

    with pytest.raises(NotFoundError):
        await get_bom(db, bom.id)


@pytest.mark.asyncio
async def test_add_bom_item(db: AsyncSession):
    bom = await create_bom(db, BOMCreate(product_id="P-01"))

    item = await add_bom_item(db, bom.id, BOMItemCreate(component_id="C-01", quantity_required=2, uom="pcs"))

    assert item.id is not None
    assert item.bom_id == bom.id
    assert item.component_id == "C-01"
    assert item.quantity_required == 2


@pytest.mark.asyncio
async def test_add_bom_item_circular_dependency(db: AsyncSession):
    bom = await create_bom(db, BOMCreate(product_id="P-01"))

    with pytest.raises(BusinessRuleError, match="A product cannot be a component of itself"):
        await add_bom_item(db, bom.id, BOMItemCreate(component_id="P-01", quantity_required=1, uom="pcs"))


@pytest.mark.asyncio
async def test_add_bom_item_circular_dependency_deep(db: AsyncSession):
    # P-01 is composed of P-02
    bom1 = await create_bom(db, BOMCreate(product_id="P-01"))
    await add_bom_item(db, bom1.id, BOMItemCreate(component_id="P-02", quantity_required=1))

    # P-02 cannot be composed of P-01
    bom2 = await create_bom(db, BOMCreate(product_id="P-02"))
    with pytest.raises(BusinessRuleError, match="Circular dependency detected"):
        await add_bom_item(db, bom2.id, BOMItemCreate(component_id="P-01", quantity_required=1))


@pytest.mark.asyncio
async def test_remove_bom_item(db: AsyncSession):
    bom = await create_bom(db, BOMCreate(product_id="P-01"))
    item = await add_bom_item(db, bom.id, BOMItemCreate(component_id="C-01", quantity_required=1))

    await remove_bom_item(db, bom.id, item.id)

    # Refresh bom
    fetched = await get_bom(db, bom.id)
    assert len(fetched.items) == 0


@pytest.mark.asyncio
async def test_remove_bom_item_not_found(db: AsyncSession):
    with pytest.raises(NotFoundError):
        await remove_bom_item(db, 999, 999)

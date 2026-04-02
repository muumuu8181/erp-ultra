import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from shared.types import Base
from shared.errors import NotFoundError, DuplicateError, BusinessRuleError
from src.foundation._011_validators.models import ValidationRule
from src.foundation._011_validators.schemas import ValidationRuleCreate, ValidationRuleUpdate
from src.foundation._011_validators import service

@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_crud_validation_rule(async_db: AsyncSession):
    # Create
    rule_data = ValidationRuleCreate(
        name="test_regex",
        description="test",
        rule_type="regex",
        parameters={"pattern": "^[0-9]+$"},
        error_message="Numbers only"
    )
    created_rule = await service.create_rule(async_db, rule_data)
    assert created_rule.id is not None
    assert created_rule.name == "test_regex"

    # Get
    fetched_rule = await service.get_rule(async_db, created_rule.id)
    assert fetched_rule.id == created_rule.id

    # List
    items, total = await service.list_rules(async_db)
    assert total == 1
    assert len(items) == 1

    # Update
    update_data = ValidationRuleUpdate(name="updated_name")
    updated_rule = await service.update_rule(async_db, created_rule.id, update_data)
    assert updated_rule.name == "updated_name"

    # Delete
    await service.delete_rule(async_db, created_rule.id)
    with pytest.raises(NotFoundError):
        await service.get_rule(async_db, created_rule.id)

@pytest.mark.asyncio
async def test_evaluate_regex(async_db: AsyncSession):
    rule = await service.create_rule(async_db, ValidationRuleCreate(
        name="number_only",
        rule_type="regex",
        parameters={"pattern": "^[0-9]+$"},
        error_message="Numbers only"
    ))

    res1 = await service.evaluate(async_db, "number_only", "123")
    assert res1.is_valid is True

    res2 = await service.evaluate(async_db, "number_only", "abc")
    assert res2.is_valid is False
    assert res2.error_message == "Numbers only"

@pytest.mark.asyncio
async def test_evaluate_range(async_db: AsyncSession):
    rule = await service.create_rule(async_db, ValidationRuleCreate(
        name="age_range",
        rule_type="range",
        parameters={"min": 18, "max": 65},
        error_message="Age out of range"
    ))

    res1 = await service.evaluate(async_db, "age_range", 30)
    assert res1.is_valid is True

    res2 = await service.evaluate(async_db, "age_range", 10)
    assert res2.is_valid is False

    res3 = await service.evaluate(async_db, "age_range", 70)
    assert res3.is_valid is False

@pytest.mark.asyncio
async def test_evaluate_length(async_db: AsyncSession):
    rule = await service.create_rule(async_db, ValidationRuleCreate(
        name="str_len",
        rule_type="length",
        parameters={"min": 2, "max": 5},
        error_message="Invalid length"
    ))

    assert (await service.evaluate(async_db, "str_len", "abc")).is_valid is True
    assert (await service.evaluate(async_db, "str_len", "a")).is_valid is False
    assert (await service.evaluate(async_db, "str_len", "abcdef")).is_valid is False

@pytest.mark.asyncio
async def test_evaluate_in(async_db: AsyncSession):
    rule = await service.create_rule(async_db, ValidationRuleCreate(
        name="status_in",
        rule_type="in",
        parameters={"choices": ["draft", "published"]},
        error_message="Invalid status"
    ))

    assert (await service.evaluate(async_db, "status_in", "draft")).is_valid is True
    assert (await service.evaluate(async_db, "status_in", "archived")).is_valid is False

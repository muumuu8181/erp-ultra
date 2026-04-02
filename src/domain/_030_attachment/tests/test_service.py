import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.domain._030_attachment.service import create_attachment, get_attachment
from src.domain._030_attachment.schemas import AttachmentCreate
from shared.types import Base

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as session:
        yield session

@pytest.mark.asyncio
async def test_create_attachment(db_session):
    data = AttachmentCreate(code="CODE-1", name="file1.txt")
    response = await create_attachment(db_session, data)
    assert response.id == 1
    assert response.code == "CODE-1"

@pytest.mark.asyncio
async def test_get_attachment(db_session):
    data = AttachmentCreate(code="CODE-2", name="file2.txt")
    created = await create_attachment(db_session, data)

    retrieved = await get_attachment(db_session, created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.code == "CODE-2"

@pytest.mark.asyncio
async def test_get_attachment_not_found(db_session):
    retrieved = await get_attachment(db_session, 999)
    assert retrieved is None

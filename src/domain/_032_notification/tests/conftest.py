import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from src.foundation._001_database import get_db
from fastapi import FastAPI
from shared.types import Base
from src.domain._032_notification.router import router

engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

app = FastAPI()
app.include_router(router)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def async_client(async_session):
    app.dependency_overrides[get_db] = lambda: async_session

    from shared.errors import ValidationError, DuplicateError, NotFoundError
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"message": exc.message})

    @app.exception_handler(DuplicateError)
    async def duplicate_error_handler(request: Request, exc: DuplicateError):
        return JSONResponse(status_code=409, content={"message": exc.message})

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"message": exc.message})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

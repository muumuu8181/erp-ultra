import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.domain._023_address.router import router
from src.foundation._001_database import get_db
from shared.errors import NotFoundError, ValidationError

app = FastAPI()

@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"message": exc.message, "code": exc.code})

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"message": exc.message, "code": exc.code, "field": exc.field})

app.include_router(router)

@pytest.fixture
async def async_client(db_session: AsyncSession):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_address_endpoint(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/addresses",
        json={
            "postal_code": "123-4567",
            "prefecture": "Tokyo",
            "city": "Shinjuku-ku",
            "street": "1-1-1"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["postal_code"] == "123-4567"
    assert data["city"] == "Shinjuku-ku"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_address_endpoint(async_client: AsyncClient) -> None:
    create_response = await async_client.post(
        "/api/v1/addresses",
        json={
            "postal_code": "123-4567",
            "prefecture": "Tokyo",
            "city": "Shinjuku-ku",
            "street": "1-1-1"
        }
    )
    address_id = create_response.json()["id"]

    response = await async_client.get(f"/api/v1/addresses/{address_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == address_id
    assert data["postal_code"] == "123-4567"

@pytest.mark.asyncio
async def test_update_address_endpoint(async_client: AsyncClient) -> None:
    create_response = await async_client.post(
        "/api/v1/addresses",
        json={
            "postal_code": "123-4567",
            "prefecture": "Tokyo",
            "city": "Shinjuku-ku",
            "street": "1-1-1"
        }
    )
    address_id = create_response.json()["id"]

    response = await async_client.put(
        f"/api/v1/addresses/{address_id}",
        json={
            "city": "Shibuya-ku",
            "street": "2-2-2"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == address_id
    assert data["city"] == "Shibuya-ku"
    assert data["street"] == "2-2-2"
    assert data["prefecture"] == "Tokyo" # Unchanged

@pytest.mark.asyncio
async def test_delete_address_endpoint(async_client: AsyncClient) -> None:
    create_response = await async_client.post(
        "/api/v1/addresses",
        json={
            "postal_code": "123-4567",
            "prefecture": "Tokyo",
            "city": "Shinjuku-ku",
            "street": "1-1-1"
        }
    )
    address_id = create_response.json()["id"]

    delete_response = await async_client.delete(f"/api/v1/addresses/{address_id}")
    assert delete_response.status_code == 204

    get_response = await async_client.get(f"/api/v1/addresses/{address_id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_list_addresses_endpoint(async_client: AsyncClient) -> None:
    for i in range(15):
        await async_client.post(
            "/api/v1/addresses",
            json={
                "postal_code": f"123-45{i:02d}",
                "prefecture": "Tokyo",
                "city": "City",
                "street": "Street"
            }
        )

    response = await async_client.get("/api/v1/addresses?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == 10
    assert data["page"] == 1
    assert data["total_pages"] == 2

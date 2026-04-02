import pytest
from httpx import AsyncClient
from src.foundation._006_logging.schemas import LogEntryCreate

@pytest.mark.asyncio
async def test_create_log_entry_endpoint(client: AsyncClient):
    data = {
        "level": "INFO",
        "message": "Test router",
        "module": "test_module"
    }
    response = await client.post("/api/v1/logging/", json=data)
    assert response.status_code == 201
    assert response.json()["level"] == "INFO"

@pytest.mark.asyncio
async def test_get_log_entries_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/logging/")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()

@pytest.mark.asyncio
async def test_get_log_entry_endpoint(client: AsyncClient):
    data = {
        "level": "INFO",
        "message": "Test get",
        "module": "test_module"
    }
    create_response = await client.post("/api/v1/logging/", json=data)
    assert create_response.status_code == 201
    log_id = create_response.json()["id"]

    get_response = await client.get(f"/api/v1/logging/{log_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == log_id

@pytest.mark.asyncio
async def test_update_log_entry_endpoint(client: AsyncClient):
    data = {
        "level": "INFO",
        "message": "Test update",
        "module": "test_module"
    }
    create_response = await client.post("/api/v1/logging/", json=data)
    assert create_response.status_code == 201
    log_id = create_response.json()["id"]

    update_data = {"level": "DEBUG"}
    update_response = await client.put(f"/api/v1/logging/{log_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["level"] == "DEBUG"

@pytest.mark.asyncio
async def test_delete_log_entry_endpoint(client: AsyncClient):
    data = {
        "level": "INFO",
        "message": "Test delete",
        "module": "test_module"
    }
    create_response = await client.post("/api/v1/logging/", json=data)
    assert create_response.status_code == 201
    log_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/logging/{log_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/logging/{log_id}")
    assert get_response.status_code == 404

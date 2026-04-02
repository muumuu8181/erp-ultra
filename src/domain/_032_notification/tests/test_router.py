import pytest
from httpx import AsyncClient
from src.domain._032_notification.models import ChannelEnum

@pytest.mark.asyncio
async def test_create_notification_template(async_client: AsyncClient):
    payload = {
        "code": "TPL_ROUTER_1",
        "name": "Router Template",
        "subject": "Router Sub",
        "body_template": "Router Body",
        "channel": "email",
        "module": "mod",
        "is_active": True
    }
    response = await async_client.post("/api/v1/notifications/notification-templates", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["code"] == "TPL_ROUTER_1"

@pytest.mark.asyncio
async def test_crud_notification_template(async_client: AsyncClient):
    payload = {
        "code": "TPL_ROUTER_CRUD",
        "name": "Router Template CRUD",
        "subject": "Router Sub",
        "body_template": "Router Body",
        "channel": "email",
        "module": "mod",
        "is_active": True
    }
    # Create
    res_create = await async_client.post("/api/v1/notifications/notification-templates", json=payload)
    assert res_create.status_code == 201
    tpl_id = res_create.json()["id"]

    # Read
    res_read = await async_client.get(f"/api/v1/notifications/notification-templates/{tpl_id}")
    assert res_read.status_code == 200
    assert res_read.json()["id"] == tpl_id

    # Update
    update_payload = {"name": "Updated Name"}
    res_update = await async_client.put(f"/api/v1/notifications/notification-templates/{tpl_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Updated Name"

    # Delete
    res_delete = await async_client.delete(f"/api/v1/notifications/notification-templates/{tpl_id}")
    assert res_delete.status_code == 204

    # Read again
    res_read_fail = await async_client.get(f"/api/v1/notifications/notification-templates/{tpl_id}")
    assert res_read_fail.status_code == 404

@pytest.mark.asyncio
async def test_list_notification_templates(async_client: AsyncClient):
    response = await async_client.get("/api/v1/notifications/notification-templates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_notification(async_client: AsyncClient):
    payload = {
        "user_id": "R1",
        "channel": "in_app",
        "subject": "Notif Sub",
        "body": "Notif Bod"
    }
    response = await async_client.post("/api/v1/notifications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["user_id"] == "R1"
    assert data["status"] == "sent"

@pytest.mark.asyncio
async def test_create_notification_validation_error(async_client: AsyncClient):
    payload = {
        "user_id": "  ", # Error
        "channel": "in_app",
        "subject": "Notif Sub",
        "body": "Notif Bod"
    }
    response = await async_client.post("/api/v1/notifications", json=payload)
    assert response.status_code == 422 # Shared error handler / ValidationError

@pytest.mark.asyncio
async def test_create_bulk_notifications(async_client: AsyncClient):
    payload = {
        "user_ids": ["B1", "B2"],
        "channel": "slack",
        "subject": "Bulk",
        "body": "Bulk message"
    }
    response = await async_client.post("/api/v1/notifications/bulk", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["user_id"] == "B1"

@pytest.mark.asyncio
async def test_list_notifications(async_client: AsyncClient):
    response = await async_client.get("/api/v1/notifications?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_get_unread_count(async_client: AsyncClient):
    response = await async_client.get("/api/v1/notifications/unread-count?user_id=R1")
    assert response.status_code == 200
    assert isinstance(response.json(), int)

@pytest.mark.asyncio
async def test_mark_as_read(async_client: AsyncClient):
    # First create
    payload = {
        "user_id": "R2",
        "channel": "in_app",
        "subject": "Sub",
        "body": "Bod"
    }
    res_create = await async_client.post("/api/v1/notifications", json=payload)
    notif_id = res_create.json()["id"]

    # Then read
    response = await async_client.post(f"/api/v1/notifications/{notif_id}/read")
    assert response.status_code == 200
    assert response.json()["status"] == "read"

@pytest.mark.asyncio
async def test_mark_all_as_read(async_client: AsyncClient):
    payload = {"user_id": "R1"}
    response = await async_client.post("/api/v1/notifications/read-all", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_get_stats(async_client: AsyncClient):
    response = await async_client.get("/api/v1/notifications/stats?user_id=R1")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "unread_count" in data

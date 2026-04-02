import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.domain._031_audit_log.router import router
from src.domain._031_audit_log.schemas import AuditLogResponse
from shared.types import PaginatedResponse

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@patch("src.domain._031_audit_log.router.create_audit_log")
def test_create_audit_log_endpoint(mock_create):
    """Test POST /api/v1/audit-log endpoint."""
    mock_create.return_value = AuditLogResponse(
        id=1,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
        action="DELETE",
        entity_name="Order",
        entity_id="789",
        user_id="admin_3",
        changes={"status": "cancelled"}
    )

    payload = {
        "action": "DELETE",
        "entity_name": "Order",
        "entity_id": "789",
        "user_id": "admin_3",
        "changes": {"status": "cancelled"}
    }

    response = client.post("/api/v1/audit-log", json=payload)

    assert response.status_code == 201
    assert response.json()["action"] == "DELETE"

@patch("src.domain._031_audit_log.router.get_audit_logs")
def test_get_audit_logs_endpoint(mock_get):
    """Test GET /api/v1/audit-log endpoint."""
    mock_get.return_value = PaginatedResponse(
        items=[
            AuditLogResponse(
                id=1,
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
                action="DELETE",
                entity_name="Order",
                entity_id="789",
                user_id="admin_3",
                changes={"status": "cancelled"}
            )
        ],
        total=1,
        page=1,
        page_size=50,
        total_pages=1
    )

    response = client.get("/api/v1/audit-log?page=1&page_size=50")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from src.sales._038_shipment.router import router
from src.sales._038_shipment import service

from fastapi import FastAPI
app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_create_shipment_route(monkeypatch):
    async def mock_create_shipment(db, data):
        from src.sales._038_shipment.models import Shipment, ShipmentItem
        from datetime import datetime
        from decimal import Decimal
        return Shipment(
            id=1,
            sales_order_id=data.sales_order_id,
            customer_id=data.customer_id,
            status=data.status,
            carrier=data.carrier,
            expected_delivery_at=data.expected_delivery_at,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            items=[ShipmentItem(id=1, shipment_id=1, product_id=1, quantity=Decimal("10.0"), created_at=datetime.now(), updated_at=datetime.now())]
        )

    monkeypatch.setattr(service, "create_shipment", mock_create_shipment)

    response = client.post("/api/v1/_038_shipment/", json={
        "sales_order_id": 1,
        "customer_id": 1,
        "items": [{"product_id": 1, "quantity": 10.0}]
    })

    assert response.status_code == 201
    assert response.json()["sales_order_id"] == 1
    assert response.json()["items"][0]["quantity"] == "10.0"

def test_get_shipment_route(monkeypatch):
    async def mock_get_shipment(db, shipment_id):
        from src.sales._038_shipment.models import Shipment
        from datetime import datetime
        return Shipment(
            id=shipment_id,
            sales_order_id=1,
            customer_id=1,
            status="draft",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            items=[]
        )

    monkeypatch.setattr(service, "get_shipment", mock_get_shipment)

    response = client.get("/api/v1/_038_shipment/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_delete_shipment_route(monkeypatch):
    async def mock_delete_shipment(db, shipment_id):
        return None

    monkeypatch.setattr(service, "delete_shipment", mock_delete_shipment)

    response = client.delete("/api/v1/_038_shipment/1")
    assert response.status_code == 204

def test_list_shipments_route(monkeypatch):
    async def mock_get_shipments(db, skip, limit):
        from src.sales._038_shipment.models import Shipment
        from datetime import datetime
        items = [
            Shipment(
                id=1, sales_order_id=1, customer_id=1, status="draft",
                created_at=datetime.now(), updated_at=datetime.now(), items=[]
            )
        ]
        return items, 1

    monkeypatch.setattr(service, "get_shipments", mock_get_shipments)

    response = client.get("/api/v1/_038_shipment/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 1
    assert data["page"] == 1

def test_update_shipment_route(monkeypatch):
    async def mock_update_shipment(db, shipment_id, data):
        from src.sales._038_shipment.models import Shipment
        from datetime import datetime
        return Shipment(
            id=shipment_id, sales_order_id=1, customer_id=1, status=data.status or "shipped",
            created_at=datetime.now(), updated_at=datetime.now(), items=[]
        )

    monkeypatch.setattr(service, "update_shipment", mock_update_shipment)

    response = client.patch("/api/v1/_038_shipment/1", json={"status": "shipped"})
    assert response.status_code == 200
    assert response.json()["status"] == "shipped"

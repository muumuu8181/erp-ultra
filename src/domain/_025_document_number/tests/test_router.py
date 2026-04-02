"""
Tests for Document Number Generator router.
"""
from datetime import date

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_router_endpoints(client: AsyncClient) -> None:
    """Test router endpoints."""
    # Create
    create_data = {
        "prefix": "INV",
        "pattern": "{prefix}-{YYYY}-{seq:05d}",
        "description": "Invoice"
    }
    response = await client.post("/api/v1/document-numbers", json=create_data)
    assert response.status_code == 201
    data = response.json()
    assert data["prefix"] == "INV"
    seq_id = data["id"]

    # Get
    response = await client.get(f"/api/v1/document-numbers/{seq_id}")
    assert response.status_code == 200
    assert response.json()["prefix"] == "INV"

    # List
    response = await client.get("/api/v1/document-numbers")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1

    # Update
    update_data = {"description": "Updated Invoice"}
    response = await client.put(f"/api/v1/document-numbers/{seq_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["description"] == "Updated Invoice"

    # Generate
    response = await client.post("/api/v1/document-numbers/generate/INV")
    assert response.status_code == 200
    gen_data = response.json()
    assert gen_data["sequence"] == 1
    today = date.today()
    assert gen_data["document_number"] == f"INV-{today.strftime('%Y')}-00001"

    # Delete
    response = await client.delete(f"/api/v1/document-numbers/{seq_id}")
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(f"/api/v1/document-numbers/{seq_id}")
    assert response.status_code == 404

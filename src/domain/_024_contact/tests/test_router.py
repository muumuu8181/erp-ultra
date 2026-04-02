import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from domain._024_contact.router import router

app = FastAPI()
app.include_router(router)

@pytest.mark.asyncio
async def test_create_contact_api(db_session):
    async def override_get_db():
        yield db_session

    from domain._024_contact.router import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/contacts/", json={
            "first_name": "API",
            "last_name": "Test",
            "email": "api@test.com"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "API"
        assert "id" in data

        # Test GET
        contact_id = data["id"]
        response = await client.get(f"/api/v1/contacts/{contact_id}")
        assert response.status_code == 200
        assert response.json()["id"] == contact_id

        # Test List
        response = await client.get("/api/v1/contacts/")
        assert response.status_code == 200
        assert response.json()["total"] >= 1

        # Test Update
        response = await client.put(f"/api/v1/contacts/{contact_id}", json={
            "first_name": "API2"
        })
        assert response.status_code == 200
        assert response.json()["first_name"] == "API2"

        # Test Delete
        response = await client.delete(f"/api/v1/contacts/{contact_id}")
        assert response.status_code == 204

        import shared.errors
        try:
            response = await client.get(f"/api/v1/contacts/{contact_id}")
            assert response.status_code in (404, 500)
        except shared.errors.NotFoundError:
            pass

    app.dependency_overrides.clear()

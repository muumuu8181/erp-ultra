import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.domain._027_warehouse_model.router import router

# A dummy app for router tests (we'll rely on the actual setup using fixtures if needed)
# In this repo, e2e usually uses the actual app, or we can use the router and a DB dependency.
# Assuming standard pytest setup in this repo injects an app or we can import it.
# Let's import the full app if available or set it up here.
from src.foundation._001_database.engine import get_db

app = FastAPI()
app.include_router(router)

@pytest.mark.asyncio
async def test_router_create_warehouse(db):
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/warehouses", json={
            "code": "R_WH01",
            "name": "Router WH",
            "type": "own"
        })
        assert res.status_code == 201
        assert res.json()["code"] == "R_WH01"
        wh_id = res.json()["id"]

        # Test get warehouse
        res2 = await client.get(f"/api/v1/warehouses/{wh_id}")
        assert res2.status_code == 200
        assert res2.json()["code"] == "R_WH01"

        # Test update warehouse
        res3 = await client.put(f"/api/v1/warehouses/{wh_id}", json={"name": "Updated R WH"})
        assert res3.status_code == 200
        assert res3.json()["name"] == "Updated R WH"

        # Test list warehouses
        res4 = await client.get("/api/v1/warehouses")
        assert res4.status_code == 200
        assert len(res4.json()["items"]) >= 1

@pytest.mark.asyncio
async def test_router_zones_and_bins(db):
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_w = await client.post("/api/v1/warehouses", json={
            "code": "R_WH02",
            "name": "Router WH 2",
            "type": "own"
        })
        wh_id = res_w.json()["id"]

        # Create zone
        res_z = await client.post(f"/api/v1/warehouses/{wh_id}/zones", json={
            "code": "Z1",
            "name": "Zone 1",
            "zone_type": "storage"
        })
        assert res_z.status_code == 201
        z_id = res_z.json()["id"]

        # List zones
        res_zl = await client.get(f"/api/v1/warehouses/{wh_id}/zones")
        assert res_zl.status_code == 200
        assert len(res_zl.json()["items"]) == 1

        # Create bin
        res_b = await client.post(f"/api/v1/zones/{z_id}/bins", json={
            "code": "B1",
            "name": "Bin 1"
        })
        assert res_b.status_code == 201

        # List bins
        res_bl = await client.get(f"/api/v1/zones/{z_id}/bins")
        assert res_bl.status_code == 200
        assert len(res_bl.json()["items"]) == 1

        # Get layout
        res_l = await client.get(f"/api/v1/warehouses/{wh_id}/layout")
        assert res_l.status_code == 200
        layout = res_l.json()
        assert layout["warehouse"]["id"] == wh_id
        assert len(layout["zones"]) == 1
        assert len(layout["zones"][0]["bins"]) == 1

import pytest
from httpx import AsyncClient

@pytest.fixture
async def create_dummy_report(client: AsyncClient):
    resp = await client.post(
        "/api/v1/sales-reports",
        json={
            "name": "Router Test",
            "report_type": "monthly_summary",
            "parameters": {}
        }
    )
    assert resp.status_code == 201
    return resp.json()

@pytest.mark.asyncio
async def test_create_report(client: AsyncClient):
    resp = await client.post(
        "/api/v1/sales-reports",
        json={
            "name": "New Report",
            "report_type": "by_region",
            "parameters": {}
        }
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Report"

@pytest.mark.asyncio
async def test_list_reports(client: AsyncClient, create_dummy_report):
    resp = await client.get("/api/v1/sales-reports")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

@pytest.mark.asyncio
async def test_get_report(client: AsyncClient, create_dummy_report):
    report_id = create_dummy_report["id"]
    resp = await client.get(f"/api/v1/sales-reports/{report_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == report_id

@pytest.mark.asyncio
async def test_execute_report(client: AsyncClient, create_dummy_report):
    report_id = create_dummy_report["id"]
    resp = await client.post(f"/api/v1/sales-reports/{report_id}/execute")
    assert resp.status_code == 200
    data = resp.json()
    assert "headers" in data
    assert "rows" in data

@pytest.mark.asyncio
async def test_export_report_csv(client: AsyncClient, create_dummy_report):
    report_id = create_dummy_report["id"]
    resp = await client.post(f"/api/v1/sales-reports/{report_id}/export-csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=report_" in resp.headers["content-disposition"]

@pytest.mark.asyncio
async def test_delete_report(client: AsyncClient, create_dummy_report):
    report_id = create_dummy_report["id"]
    resp = await client.delete(f"/api/v1/sales-reports/{report_id}")
    assert resp.status_code == 200

    # Verify deletion (API doesn't have an exception handler in our local fast API wrapper, so catch the native error)
    import shared.errors
    with pytest.raises(shared.errors.NotFoundError):
        await client.get(f"/api/v1/sales-reports/{report_id}")

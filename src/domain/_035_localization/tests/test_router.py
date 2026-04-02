"""
Tests for localization router.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain._035_localization.router import router
from src.foundation._001_database.engine import get_db

app = FastAPI()
app.include_router(router)


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_locales_endpoints(client: AsyncClient, db: AsyncSession):
    # Ensure seed locales exist
    res = await client.get("/api/v1/localization/locales")
    assert res.status_code == 200
    assert len(res.json()) >= 2

    # Create new
    payload = {
        "code": "es-MX",
        "name": "Spanish (Mexico)",
        "language": "es",
        "country": "MX",
        "date_format": "%d/%m/%Y",
        "number_format": "#,###.##",
        "currency_code": "MXN",
        "is_active": True
    }
    create_res = await client.post("/api/v1/localization/locales", json=payload)
    assert create_res.status_code == 201
    assert create_res.json()["code"] == "es-MX"

    # Invalid create
    bad_payload = payload.copy()
    bad_payload["code"] = "es-mexico"
    bad_res = await client.post("/api/v1/localization/locales", json=bad_payload)
    assert bad_res.status_code == 422


@pytest.mark.asyncio
async def test_translations_endpoints(client: AsyncClient, db: AsyncSession):
    # Add translation (using pre-seeded en-US)
    locales_res = await client.get("/api/v1/localization/locales")
    en_us_id = next(loc["id"] for loc in locales_res.json() if loc["code"] == "en-US")

    trans_payload = {
        "locale_id": en_us_id,
        "module": "core",
        "key": "core.test.endpoint",
        "value": "Endpoint Test"
    }

    post_res = await client.post("/api/v1/localization/translations", json=trans_payload)
    assert post_res.status_code == 201
    assert post_res.json()["value"] == "Endpoint Test"

    # Get translations
    get_res = await client.get("/api/v1/localization/translations?locale=en-US&module=core")
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1

    # Lookup
    lookup_payload = {
        "locale_code": "en-US",
        "module": "core",
        "key": "core.test.endpoint",
        "default": "Default"
    }
    lookup_res = await client.post("/api/v1/localization/translations/lookup", json=lookup_payload)
    assert lookup_res.status_code == 200
    assert lookup_res.json()["value"] == "Endpoint Test"


@pytest.mark.asyncio
async def test_format_endpoints(client: AsyncClient, db: AsyncSession):
    # Wait for seed to finish if necessary by calling GET locales
    await client.get("/api/v1/localization/locales")

    date_res = await client.post("/api/v1/localization/format-date", json={
        "locale_code": "ja-JP",
        "value": "2025-01-15"
    })
    assert date_res.status_code == 200
    assert date_res.json()["formatted"] == "2025年01月15日"

    num_res = await client.post("/api/v1/localization/format-number", json={
        "locale_code": "ja-JP",
        "value": 1234567.89
    })
    assert num_res.status_code == 200
    assert num_res.json()["formatted"] == "1,234,568"

    cur_res = await client.post("/api/v1/localization/format-currency", json={
        "locale_code": "ja-JP",
        "value": 100000
    })
    assert cur_res.status_code == 200
    assert cur_res.json()["formatted"] == "¥100,000"


@pytest.mark.asyncio
async def test_import_export_endpoints(client: AsyncClient, db: AsyncSession):
    # Ensure seed
    await client.get("/api/v1/localization/locales")

    import_payload = {
        "locale_code": "ja-JP",
        "module": "invoice",
        "translations": {
            "invoice.title.main": "請求書",
            "invoice.status.paid": "支払済"
        }
    }

    import_res = await client.post("/api/v1/localization/translations/import", json=import_payload)
    assert import_res.status_code == 200
    assert import_res.json()["imported_count"] == 2

    export_payload = {
        "locale_code": "ja-JP",
        "module": "invoice"
    }
    export_res = await client.post("/api/v1/localization/translations/export", json=export_payload)
    assert export_res.status_code == 200
    data = export_res.json()
    assert data["locale_code"] == "ja-JP"
    assert data["translations"]["invoice.title.main"] == "請求書"

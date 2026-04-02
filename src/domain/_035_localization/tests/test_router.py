import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.foundation._001_database.engine import get_db
from src.domain._035_localization import service
from src.domain._035_localization.router import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seeded_db(db: AsyncSession):
    await service.seed_locales(db)
    return db


@pytest.fixture
async def client(seeded_db):
    app.dependency_overrides[get_db] = lambda: seeded_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_create_locale(client):
    resp = await client.post(
        "/api/v1/localization/locales",
        json={
            "code": "fr-FR",
            "name": "French",
            "language": "fr",
            "country": "FR",
            "date_format": "%d/%m/%Y",
            "number_format": "# ###,##",
            "currency_code": "EUR",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "fr-FR"


async def test_create_locale_validation_error(client):
    resp = await client.post(
        "/api/v1/localization/locales",
        json={
            "code": "invalid",
            "name": "French",
            "language": "fr",
            "country": "FR",
            "date_format": "%d/%m/%Y",
            "number_format": "# ###,##",
            "currency_code": "EUR",
        },
    )
    assert resp.status_code == 422


async def test_list_locales(client):
    resp = await client.get("/api/v1/localization/locales")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    codes = [d["code"] for d in data]
    assert "ja-JP" in codes


async def test_add_translation(client):
    resp_loc = await client.get("/api/v1/localization/locales")
    l_id = next(loc["id"] for loc in resp_loc.json() if loc["code"] == "ja-JP")

    resp = await client.post(
        "/api/v1/localization/translations",
        json={"locale_id": l_id, "module": "inv", "key": "inv.title.main", "value": "請求書"},
    )
    assert resp.status_code == 201


async def test_get_translations(client):
    resp = await client.get("/api/v1/localization/translations?locale=ja-JP")
    assert resp.status_code == 200


async def test_lookup_translation(client):
    resp = await client.post(
        "/api/v1/localization/translations/lookup",
        json={"locale_code": "ja-JP", "key": "unknown.key.val", "default": "Default"},
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == "Default"


async def test_format_date(client):
    resp = await client.post(
        "/api/v1/localization/localization/format-date", json={"locale_code": "ja-JP", "value": "2025-01-15"}
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == "2025年01月15日"


async def test_format_number(client):
    resp = await client.post(
        "/api/v1/localization/localization/format-number", json={"locale_code": "ja-JP", "value": 1234567.89}
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == "1,234,567"


async def test_format_currency(client):
    resp = await client.post(
        "/api/v1/localization/localization/format-currency", json={"locale_code": "ja-JP", "value": 100000}
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == "¥100,000"


async def test_export_import(client):
    resp_import = await client.post(
        "/api/v1/localization/translations/import",
        json={"locale_code": "ja-JP", "module": "inv", "translations": {"inv.title.main": "請求書"}},
    )
    assert resp_import.status_code == 200
    assert resp_import.json()["imported_count"] == 1

    resp_export = await client.post(
        "/api/v1/localization/translations/export", json={"locale_code": "ja-JP", "module": "inv"}
    )
    assert resp_export.status_code == 200
    assert resp_export.json()["translations"]["inv.title.main"] == "請求書"

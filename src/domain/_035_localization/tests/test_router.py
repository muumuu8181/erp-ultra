import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain._035_localization.service import seed_default_locales
from src.domain._035_localization.models import Locale

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seeded_db_router(db_session: AsyncSession):
    await seed_default_locales(db_session)
    return db_session


async def test_create_locale(client: AsyncClient, seeded_db_router: AsyncSession):
    data = {
        "code": "fr-FR",
        "name": "Français",
        "language": "fr",
        "country": "FR",
        "date_format": "%d/%m/%Y",
        "number_format": "#,###.##",
        "currency_code": "EUR"
    }
    response = await client.post("/api/v1/localization/locales", json=data)
    assert response.status_code == 201
    assert response.json()["code"] == "fr-FR"


async def test_list_locales(client: AsyncClient, seeded_db_router: AsyncSession):
    response = await client.get("/api/v1/localization/locales")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


async def test_add_translation(client: AsyncClient, seeded_db_router: AsyncSession):
    # Need to get a locale ID first
    resp = await client.get("/api/v1/localization/locales")
    locales = resp.json()
    ja_id = next(l["id"] for l in locales if l["code"] == "ja-JP")

    data = {
        "locale_id": ja_id,
        "module": "invoice",
        "key": "invoice.title.main",
        "value": "請求書"
    }
    response = await client.post("/api/v1/localization/translations", json=data)
    assert response.status_code == 201
    assert response.json()["value"] == "請求書"


async def test_get_translations(client: AsyncClient, seeded_db_router: AsyncSession):
    # Seed a translation
    resp = await client.get("/api/v1/localization/locales")
    locales = resp.json()
    ja_id = next(l["id"] for l in locales if l["code"] == "ja-JP")

    await client.post("/api/v1/localization/translations", json={
        "locale_id": ja_id,
        "module": "invoice",
        "key": "invoice.title.main",
        "value": "請求書"
    })

    response = await client.get("/api/v1/localization/translations?locale=ja-JP&module=invoice")
    assert response.status_code == 200
    assert len(response.json()) >= 1


async def test_lookup_translation(client: AsyncClient, seeded_db_router: AsyncSession):
    data = {
        "locale_code": "ja-JP",
        "key": "invoice.title.main",
        "default": "Invoice"
    }
    response = await client.post("/api/v1/localization/translations/lookup", json=data)
    assert response.status_code == 200
    assert response.json() == "Invoice" # Since it doesn't exist yet, it returns default


async def test_format_date(client: AsyncClient, seeded_db_router: AsyncSession):
    data = {
        "locale_code": "ja-JP",
        "value": "2025-01-15"
    }
    response = await client.post("/api/v1/localization/format-date", json=data)
    assert response.status_code == 200
    assert response.json() == "2025年01月15日"


async def test_format_number(client: AsyncClient, seeded_db_router: AsyncSession):
    data = {
        "locale_code": "ja-JP",
        "value": 1234567.89
    }
    response = await client.post("/api/v1/localization/format-number", json=data)
    assert response.status_code == 200
    assert response.json() == "1,234,567"


async def test_format_currency(client: AsyncClient, seeded_db_router: AsyncSession):
    data = {
        "locale_code": "ja-JP",
        "value": 100000
    }
    response = await client.post("/api/v1/localization/format-currency", json=data)
    assert response.status_code == 200
    assert response.json() == "¥100,000"


async def test_export_translations(client: AsyncClient, seeded_db_router: AsyncSession):
    response = await client.post("/api/v1/localization/translations/export?locale_code=ja-JP&module=invoice")
    assert response.status_code == 200
    assert "translations" in response.json()


async def test_import_translations(client: AsyncClient, seeded_db_router: AsyncSession):
    data = {
        "locale_code": "ja-JP",
        "module": "invoice",
        "translations": {
            "invoice.title.main": "請求書",
            "invoice.label.date": "日付"
        }
    }
    response = await client.post("/api/v1/localization/translations/import", json=data)
    assert response.status_code == 200
    assert response.json()["imported_count"] == 2

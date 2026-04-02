import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain._035_localization.service import seed_default_locales

pytestmark = pytest.mark.asyncio

async def test_create_locale_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/localization/locales", json={
        "code": "zh-CN",
        "name": "Chinese",
        "language": "zh",
        "country": "CN",
        "date_format": "%Y-%m-%d",
        "number_format": "#,###.##",
        "currency_code": "CNY"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "zh-CN"

async def test_list_locales_endpoint(client: AsyncClient, db_session: AsyncSession):
    await seed_default_locales(db_session)
    response = await client.get("/api/v1/localization/locales")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    codes = [l["code"] for l in data]
    assert "ja-JP" in codes

async def test_add_translation_endpoint(client: AsyncClient, db_session: AsyncSession):
    await seed_default_locales(db_session)
    response = await client.get("/api/v1/localization/locales")
    locales = response.json()
    ja_locale = next(l for l in locales if l["code"] == "ja-JP")

    response = await client.post("/api/v1/localization/translations", json={
        "locale_id": ja_locale["id"],
        "module": "test",
        "key": "test.key.name",
        "value": "テスト"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == "テスト"

async def test_get_translations_endpoint(client: AsyncClient, db_session: AsyncSession):
    await seed_default_locales(db_session)
    # Add translation directly
    response = await client.get("/api/v1/localization/locales")
    locales = response.json()
    en_locale = next(l for l in locales if l["code"] == "en-US")

    await client.post("/api/v1/localization/translations", json={
        "locale_id": en_locale["id"],
        "module": "sales",
        "key": "sales.order.title",
        "value": "Sales Order"
    })

    response = await client.get("/api/v1/localization/translations?locale=en-US&module=sales")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["key"] == "sales.order.title"

async def test_lookup_translation_endpoint(client: AsyncClient, db_session: AsyncSession):
    await seed_default_locales(db_session)
    response = await client.post("/api/v1/localization/translations/lookup", json={
        "locale_code": "en-US",
        "key": "non.existent.key",
        "default": "Default Value"
    })
    assert response.status_code == 200
    assert response.json() == "Default Value"

async def test_format_date_endpoint(client: AsyncClient, db_session: AsyncSession):
    await seed_default_locales(db_session)
    response = await client.post("/api/v1/localization/format-date", json={
        "locale_code": "ja-JP",
        "value": "2025-01-15"
    })
    assert response.status_code == 200
    assert response.json() == "2025年01月15日"

async def test_format_number_endpoint(client: AsyncClient, db_session: AsyncSession):
    await seed_default_locales(db_session)
    response = await client.post("/api/v1/localization/format-number", json={
        "locale_code": "en-US",
        "value": 1234567.89
    })
    assert response.status_code == 200
    assert response.json() == "1,234,567.89"

async def test_format_currency_endpoint(client: AsyncClient, db_session: AsyncSession):
    await seed_default_locales(db_session)
    response = await client.post("/api/v1/localization/format-currency", json={
        "locale_code": "ja-JP",
        "value": 100000
    })
    assert response.status_code == 200
    assert response.json() == "¥100,000"

async def test_export_import_endpoints(client: AsyncClient, db_session: AsyncSession):
    await seed_default_locales(db_session)

    # Import
    response = await client.post("/api/v1/localization/translations/import", json={
        "locale_code": "ja-JP",
        "module": "settings",
        "translations": {
            "settings.title.main": "設定",
            "settings.button.save": "保存"
        }
    })
    assert response.status_code == 200
    assert response.json()["imported"] == 2

    # Export
    response = await client.post("/api/v1/localization/translations/export", json={
        "locale_code": "ja-JP",
        "module": "settings"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["locale_code"] == "ja-JP"
    assert data["translations"]["settings.button.save"] == "保存"

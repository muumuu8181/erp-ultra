import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain._035_localization.models import Locale


@pytest.fixture
async def seeded_locale(db: AsyncSession) -> Locale:
    locale = Locale(
        code="ja-JP",
        name="日本語",
        language="ja",
        country="JP",
        date_format="%Y年%m月%d日",
        number_format="#,###",
        currency_code="JPY"
    )
    db.add(locale)
    await db.commit()
    await db.refresh(locale)
    return locale


@pytest.mark.asyncio
async def test_api_create_locale(async_client: AsyncClient):
    payload = {
        "code": "es-ES",
        "name": "Spanish",
        "language": "es",
        "country": "ES",
        "date_format": "%d/%m/%Y",
        "number_format": "#.###,##",
        "currency_code": "EUR"
    }
    response = await async_client.post("/api/v1/localization/locales", json=payload)
    assert response.status_code == 201
    assert response.json()["code"] == "es-ES"


@pytest.mark.asyncio
async def test_api_list_locales(async_client: AsyncClient, seeded_locale: Locale):
    response = await async_client.get("/api/v1/localization/locales")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_api_add_translation(async_client: AsyncClient, seeded_locale: Locale):
    payload = {
        "locale_id": seeded_locale.id,
        "module": "invoice",
        "key": "invoice.title.main",
        "value": "請求書"
    }
    response = await async_client.post("/api/v1/localization/translations", json=payload)
    assert response.status_code == 201
    assert response.json()["key"] == "invoice.title.main"


@pytest.mark.asyncio
async def test_api_get_translations(async_client: AsyncClient, seeded_locale: Locale):
    # insert first
    await async_client.post("/api/v1/localization/translations", json={
        "locale_id": seeded_locale.id,
        "module": "invoice",
        "key": "invoice.title.main",
        "value": "請求書"
    })

    response = await async_client.get("/api/v1/localization/translations?locale=ja-JP")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_api_translate(async_client: AsyncClient, seeded_locale: Locale):
    await async_client.post("/api/v1/localization/translations", json={
        "locale_id": seeded_locale.id,
        "module": "invoice",
        "key": "invoice.title.main",
        "value": "請求書"
    })

    payload = {
        "locale_code": "ja-JP",
        "key": "invoice.title.main",
        "default": "Invoice"
    }
    response = await async_client.post("/api/v1/localization/translations/lookup", json=payload)
    assert response.status_code == 200
    assert response.json() == "請求書"


@pytest.mark.asyncio
async def test_api_format_date(async_client: AsyncClient, seeded_locale: Locale):
    payload = {
        "locale_code": "ja-JP",
        "value": "2025-01-15"
    }
    response = await async_client.post("/api/v1/localization/format-date", json=payload)
    assert response.status_code == 200
    assert response.json() == "2025年01月15日"


@pytest.mark.asyncio
async def test_api_format_number(async_client: AsyncClient, seeded_locale: Locale):
    payload = {
        "locale_code": "ja-JP",
        "value": 1234567.89
    }
    response = await async_client.post("/api/v1/localization/format-number", json=payload)
    assert response.status_code == 200
    assert response.json() == "1,234,567"


@pytest.mark.asyncio
async def test_api_format_currency(async_client: AsyncClient, seeded_locale: Locale):
    payload = {
        "locale_code": "ja-JP",
        "value": 100000
    }
    response = await async_client.post("/api/v1/localization/format-currency", json=payload)
    assert response.status_code == 200
    assert response.json() == "¥100,000"


@pytest.mark.asyncio
async def test_api_export_translations(async_client: AsyncClient, seeded_locale: Locale):
    await async_client.post("/api/v1/localization/translations", json={
        "locale_id": seeded_locale.id,
        "module": "invoice",
        "key": "invoice.title.main",
        "value": "請求書"
    })

    payload = {
        "locale_code": "ja-JP",
        "module": "invoice"
    }
    response = await async_client.post("/api/v1/localization/translations/export", json=payload)
    assert response.status_code == 200
    assert response.json()["locale_code"] == "ja-JP"
    assert "invoice.title.main" in response.json()["translations"]


@pytest.mark.asyncio
async def test_api_import_translations(async_client: AsyncClient, seeded_locale: Locale):
    payload = {
        "locale_code": "ja-JP",
        "module": "invoice",
        "translations": {
            "invoice.title.main": "請求書",
            "invoice.status.draft": "下書き"
        }
    }
    response = await async_client.post("/api/v1/localization/translations/import", json=payload)
    assert response.status_code == 200
    assert response.json() == 2


@pytest.mark.asyncio
async def test_validation_errors(async_client: AsyncClient):
    # Test 422 on invalid locale format in create
    payload = {
        "code": "japanese", # invalid
        "name": "Japanese",
        "language": "ja",
        "country": "JP",
        "date_format": "%d/%m/%Y",
        "number_format": "#.###,##",
        "currency_code": "JPY"
    }
    response = await async_client.post("/api/v1/localization/locales", json=payload)
    assert response.status_code == 422
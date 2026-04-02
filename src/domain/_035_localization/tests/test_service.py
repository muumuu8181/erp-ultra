from datetime import date
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError, DuplicateError, NotFoundError
from src.domain._035_localization.schemas import LocaleCreate, TranslationCreate
from src.domain._035_localization.service import (
    create_locale,
    list_locales,
    add_translation,
    get_translations,
    get_translations_by_module,
    translate,
    format_date,
    format_number,
    format_currency,
    export_translations,
    import_translations,
)
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

    locale_us = Locale(
        code="en-US",
        name="English",
        language="en",
        country="US",
        date_format="%m/%d/%Y",
        number_format="#,###.##",
        currency_code="USD"
    )
    db.add(locale_us)
    await db.commit()
    await db.refresh(locale)
    return locale


@pytest.mark.asyncio
async def test_create_locale_success(db: AsyncSession):
    data = LocaleCreate(
        code="zh-CN",
        name="Chinese",
        language="zh",
        country="CN",
        date_format="%Y-%m-%d",
        number_format="#,###.##",
        currency_code="CNY"
    )
    locale = await create_locale(db, data)
    assert locale.id is not None
    assert locale.code == "zh-CN"


@pytest.mark.asyncio
async def test_create_locale_invalid_format(db: AsyncSession):
    data = LocaleCreate(
        code="zh_CN", # invalid format
        name="Chinese",
        language="zh",
        country="CN",
        date_format="%Y-%m-%d",
        number_format="#,###.##",
        currency_code="CNY"
    )
    with pytest.raises(ValidationError):
        await create_locale(db, data)


@pytest.mark.asyncio
async def test_create_locale_duplicate_code(db: AsyncSession, seeded_locale: Locale):
    data = LocaleCreate(
        code="ja-JP", # duplicate
        name="Japanese 2",
        language="ja",
        country="JP",
        date_format="%Y-%m-%d",
        number_format="#,###",
        currency_code="JPY"
    )
    with pytest.raises(DuplicateError):
        await create_locale(db, data)


@pytest.mark.asyncio
async def test_list_locales(db: AsyncSession, seeded_locale: Locale):
    locales = await list_locales(db)
    assert len(locales) >= 2

    active_locales = await list_locales(db, is_active=True)
    assert len(active_locales) == len(locales)


@pytest.mark.asyncio
async def test_add_translation_success(db: AsyncSession, seeded_locale: Locale):
    data = TranslationCreate(
        locale_id=seeded_locale.id,
        module="invoice",
        key="invoice.title.main",
        value="請求書"
    )
    translation = await add_translation(db, data)
    assert translation.id is not None
    assert translation.key == "invoice.title.main"


@pytest.mark.asyncio
async def test_add_translation_invalid_key_format(db: AsyncSession, seeded_locale: Locale):
    data = TranslationCreate(
        locale_id=seeded_locale.id,
        module="invoice",
        key="InvoiceTitle", # invalid format
        value="請求書"
    )
    with pytest.raises(ValidationError):
        await add_translation(db, data)


@pytest.mark.asyncio
async def test_add_translation_empty_value(db: AsyncSession, seeded_locale: Locale):
    data = TranslationCreate(
        locale_id=seeded_locale.id,
        module="invoice",
        key="invoice.title.main",
        value="   " # empty
    )
    with pytest.raises(ValidationError):
        await add_translation(db, data)


@pytest.mark.asyncio
async def test_get_translations(db: AsyncSession, seeded_locale: Locale):
    # refresh seeded_locale explicitly to avoid lazy loading issues across async calls
    await db.refresh(seeded_locale)
    locale_id = seeded_locale.id

    await add_translation(db, TranslationCreate(locale_id=locale_id, module="invoice", key="invoice.title.main", value="請求書"))
    await add_translation(db, TranslationCreate(locale_id=locale_id, module="sales", key="sales.order.new", value="新規受注"))

    translations = await get_translations(db, "ja-JP")
    assert len(translations) >= 2


@pytest.mark.asyncio
async def test_get_translations_filtered_by_module(db: AsyncSession, seeded_locale: Locale):
    await db.refresh(seeded_locale)
    locale_id = seeded_locale.id

    await add_translation(db, TranslationCreate(locale_id=locale_id, module="invoice", key="invoice.title.main", value="請求書"))
    await add_translation(db, TranslationCreate(locale_id=locale_id, module="sales", key="sales.order.new", value="新規受注"))

    translations = await get_translations(db, "ja-JP", module="invoice")
    assert len(translations) >= 1
    assert any(t.key == "invoice.title.main" for t in translations)


@pytest.mark.asyncio
async def test_get_translations_by_module(db: AsyncSession, seeded_locale: Locale):
    await db.refresh(seeded_locale)
    locale_id = seeded_locale.id
    await add_translation(db, TranslationCreate(locale_id=locale_id, module="invoice", key="invoice.title.main", value="請求書"))

    translations_dict = await get_translations_by_module(db, "ja-JP", "invoice")
    assert isinstance(translations_dict, dict)
    assert translations_dict["invoice.title.main"] == "請求書"


@pytest.mark.asyncio
async def test_translate(db: AsyncSession, seeded_locale: Locale):
    await db.refresh(seeded_locale)
    locale_id = seeded_locale.id
    await add_translation(db, TranslationCreate(locale_id=locale_id, module="invoice", key="invoice.title.main", value="請求書"))

    # existing key
    val = await translate(db, "ja-JP", "invoice.title.main")
    assert val == "請求書"

    # missing key returns default
    val_default = await translate(db, "ja-JP", "invoice.missing.key", default="Missing")
    assert val_default == "Missing"

    # no default returns key
    val_key = await translate(db, "ja-JP", "invoice.missing.key")
    assert val_key == "invoice.missing.key"


@pytest.mark.asyncio
async def test_format_date(db: AsyncSession, seeded_locale: Locale):
    test_date = date(2025, 1, 15)
    formatted_ja = await format_date(db, "ja-JP", test_date)
    assert formatted_ja == "2025年01月15日"

    formatted_en = await format_date(db, "en-US", test_date)
    assert formatted_en == "01/15/2025"


@pytest.mark.asyncio
async def test_format_number(db: AsyncSession, seeded_locale: Locale):
    test_val = 1234567.89
    formatted_ja = await format_number(db, "ja-JP", test_val)
    assert formatted_ja == "1,234,567"

    formatted_en = await format_number(db, "en-US", test_val)
    assert formatted_en == "1,234,567.89"


@pytest.mark.asyncio
async def test_format_currency(db: AsyncSession, seeded_locale: Locale):
    test_val = 100000
    formatted_ja = await format_currency(db, "ja-JP", test_val)
    assert formatted_ja == "¥100,000"

    formatted_en = await format_currency(db, "en-US", 100000.5)
    assert formatted_en == "$100,000.50"


@pytest.mark.asyncio
async def test_export_translations(db: AsyncSession, seeded_locale: Locale):
    await db.refresh(seeded_locale)
    locale_id = seeded_locale.id
    await add_translation(db, TranslationCreate(locale_id=locale_id, module="invoice", key="invoice.title.main", value="請求書"))

    export_data = await export_translations(db, "ja-JP", module="invoice")
    assert export_data.locale_code == "ja-JP"
    assert export_data.translations == {"invoice.title.main": "請求書"}


@pytest.mark.asyncio
async def test_import_translations(db: AsyncSession, seeded_locale: Locale):
    # creates new entries
    count = await import_translations(
        db, "ja-JP", {"invoice.title.main": "請求書", "invoice.status.draft": "下書き"}, "invoice"
    )
    assert count == 2

    translations = await get_translations_by_module(db, "ja-JP", "invoice")
    assert translations["invoice.title.main"] == "請求書"

    # updates existing entries
    count2 = await import_translations(
        db, "ja-JP", {"invoice.title.main": "請求書 (更新)"}, "invoice"
    )
    assert count2 == 1
    translations_updated = await get_translations_by_module(db, "ja-JP", "invoice")
    assert translations_updated["invoice.title.main"] == "請求書 (更新)"

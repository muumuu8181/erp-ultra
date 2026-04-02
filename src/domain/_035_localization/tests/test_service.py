import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.errors import ValidationError, DuplicateError, NotFoundError
from src.domain._035_localization.models import Locale, Translation
from src.domain._035_localization.schemas import LocaleCreate, TranslationCreate
from src.domain._035_localization.service import (
    create_locale, list_locales, add_translation, get_translations,
    get_translations_by_module, translate, format_date, format_number,
    format_currency, export_translations, import_translations, seed_default_locales
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seeded_db(db_session: AsyncSession):
    await seed_default_locales(db_session)
    return db_session


async def test_create_locale_success(db_session: AsyncSession):
    data = LocaleCreate(
        code="fr-FR", name="Français", language="fr", country="FR",
        date_format="%d/%m/%Y", number_format="#,###.##", currency_code="EUR"
    )
    locale = await create_locale(db_session, data)
    assert locale.id is not None
    assert locale.code == "fr-FR"


async def test_list_locales(seeded_db: AsyncSession):
    locales = await list_locales(seeded_db)
    assert len(locales) >= 2
    codes = [l.code for l in locales]
    assert "ja-JP" in codes
    assert "en-US" in codes

    active_locales = await list_locales(seeded_db, is_active=True)
    assert len(active_locales) == len(locales)


async def test_add_translation(seeded_db: AsyncSession):
    locales = await list_locales(seeded_db)
    ja_locale = next(l for l in locales if l.code == "ja-JP")

    data = TranslationCreate(
        locale_id=ja_locale.id, module="invoice", key="invoice.title.main", value="請求書"
    )
    trans = await add_translation(seeded_db, data)
    assert trans.id is not None
    assert trans.value == "請求書"


async def test_get_translations(seeded_db: AsyncSession):
    locales = await list_locales(seeded_db)
    en_locale = next(l for l in locales if l.code == "en-US")

    await add_translation(seeded_db, TranslationCreate(
        locale_id=en_locale.id, module="common", key="common.button.save", value="Save"
    ))
    await add_translation(seeded_db, TranslationCreate(
        locale_id=en_locale.id, module="invoice", key="invoice.title.main", value="Invoice"
    ))

    # All for locale
    all_trans = await get_translations(seeded_db, "en-US")
    assert len(all_trans) == 2

    # Filtered by module
    invoice_trans = await get_translations(seeded_db, "en-US", module="invoice")
    assert len(invoice_trans) == 1
    assert invoice_trans[0].value == "Invoice"


async def test_get_translations_by_module(seeded_db: AsyncSession):
    locales = await list_locales(seeded_db)
    ja_locale = next(l for l in locales if l.code == "ja-JP")

    await add_translation(seeded_db, TranslationCreate(
        locale_id=ja_locale.id, module="common", key="common.button.save", value="保存"
    ))

    dict_trans = await get_translations_by_module(seeded_db, "ja-JP", "common")
    assert "common.button.save" in dict_trans
    assert dict_trans["common.button.save"] == "保存"


async def test_translate(seeded_db: AsyncSession):
    locales = await list_locales(seeded_db)
    ja_locale = next(l for l in locales if l.code == "ja-JP")

    await add_translation(seeded_db, TranslationCreate(
        locale_id=ja_locale.id, module="common", key="common.msg.success", value="成功"
    ))

    # Existing
    val = await translate(seeded_db, "ja-JP", "common.msg.success")
    assert val == "成功"

    # Missing with default
    val2 = await translate(seeded_db, "ja-JP", "common.msg.error", default="Error")
    assert val2 == "Error"

    # Missing without default
    val3 = await translate(seeded_db, "ja-JP", "common.msg.warning")
    assert val3 == "common.msg.warning"

    # Missing locale
    val4 = await translate(seeded_db, "fr-FR", "common.msg.success", default="Success")
    assert val4 == "Success"


async def test_format_date(seeded_db: AsyncSession):
    dt = date(2025, 1, 15)

    ja_date = await format_date(seeded_db, "ja-JP", dt)
    assert ja_date == "2025年01月15日"

    en_date = await format_date(seeded_db, "en-US", dt)
    assert en_date == "01/15/2025"


async def test_format_number(seeded_db: AsyncSession):
    val = 1234567.89

    ja_num = await format_number(seeded_db, "ja-JP", val)
    assert ja_num == "1,234,567"

    en_num = await format_number(seeded_db, "en-US", val)
    assert en_num == "1,234,567.89"


async def test_format_currency(seeded_db: AsyncSession):
    val = 100000.50

    ja_curr = await format_currency(seeded_db, "ja-JP", val)
    assert ja_curr == "¥100,000"

    en_curr = await format_currency(seeded_db, "en-US", val)
    assert en_curr == "$100,000.50"


async def test_export_translations(seeded_db: AsyncSession):
    locales = await list_locales(seeded_db)
    ja_locale = next(l for l in locales if l.code == "ja-JP")

    await add_translation(seeded_db, TranslationCreate(
        locale_id=ja_locale.id, module="invoice", key="invoice.title.main", value="請求書"
    ))

    export = await export_translations(seeded_db, "ja-JP", module="invoice")
    assert export.locale_code == "ja-JP"
    assert export.translations["invoice.title.main"] == "請求書"


async def test_import_translations(seeded_db: AsyncSession):
    data = {
        "invoice.title.main": "Invoice",
        "invoice.button.send": "Send"
    }

    count = await import_translations(seeded_db, "en-US", data, "invoice")
    assert count == 2

    # Upsert test
    data_update = {
        "invoice.title.main": "Tax Invoice",
        "invoice.label.date": "Date"
    }
    count2 = await import_translations(seeded_db, "en-US", data_update, "invoice")
    assert count2 == 2

    dict_trans = await get_translations_by_module(seeded_db, "en-US", "invoice")
    assert dict_trans["invoice.title.main"] == "Tax Invoice"
    assert dict_trans["invoice.button.send"] == "Send"
    assert dict_trans["invoice.label.date"] == "Date"

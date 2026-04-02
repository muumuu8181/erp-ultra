import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, NotFoundError, ValidationError
from src.domain._035_localization.models import Locale, Translation
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
    seed_default_locales
)

pytestmark = pytest.mark.asyncio

async def test_seed_default_locales(db_session: AsyncSession):
    await seed_default_locales(db_session)
    locales = await list_locales(db_session)
    codes = [l.code for l in locales]
    assert "ja-JP" in codes
    assert "en-US" in codes

async def test_create_locale(db_session: AsyncSession):
    data = LocaleCreate(
        code="fr-FR",
        name="Français",
        language="fr",
        country="FR",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    locale = await create_locale(db_session, data)
    assert locale.id is not None
    assert locale.code == "fr-FR"

    # Duplicate
    with pytest.raises(DuplicateError):
        await create_locale(db_session, data)

async def test_add_translation(db_session: AsyncSession):
    await seed_default_locales(db_session)
    locales = await list_locales(db_session)
    ja_locale = next(l for l in locales if l.code == "ja-JP")

    data = TranslationCreate(
        locale_id=ja_locale.id,
        module="invoice",
        key="invoice.title.main",
        value="請求書"
    )
    trans = await add_translation(db_session, data)
    assert trans.id is not None
    assert trans.value == "請求書"

    # Duplicate
    with pytest.raises(DuplicateError):
        await add_translation(db_session, data)

async def test_translate(db_session: AsyncSession):
    await seed_default_locales(db_session)
    locales = await list_locales(db_session)
    en_locale = next(l for l in locales if l.code == "en-US")

    await add_translation(db_session, TranslationCreate(
        locale_id=en_locale.id,
        module="sales",
        key="sales.order.title",
        value="Sales Order"
    ))

    val = await translate(db_session, "en-US", "sales.order.title")
    assert val == "Sales Order"

    # Default fallback
    val_default = await translate(db_session, "en-US", "sales.missing.key", "Default Title")
    assert val_default == "Default Title"

    # Key fallback
    val_key = await translate(db_session, "en-US", "sales.missing.key")
    assert val_key == "sales.missing.key"

async def test_format_date(db_session: AsyncSession):
    await seed_default_locales(db_session)
    d = date(2025, 1, 15)

    ja_str = await format_date(db_session, "ja-JP", d)
    assert ja_str == "2025年01月15日"

    en_str = await format_date(db_session, "en-US", d)
    assert en_str == "01/15/2025"

async def test_format_number(db_session: AsyncSession):
    await seed_default_locales(db_session)
    num = 1234567.89

    ja_str = await format_number(db_session, "ja-JP", num)
    assert ja_str == "1,234,567"

    en_str = await format_number(db_session, "en-US", num)
    assert en_str == "1,234,567.89"

async def test_format_currency(db_session: AsyncSession):
    await seed_default_locales(db_session)
    val = 100000.50

    ja_str = await format_currency(db_session, "ja-JP", val)
    assert ja_str == "¥100,000"

    en_str = await format_currency(db_session, "en-US", val)
    assert en_str == "$100,000.50"

async def test_import_export_translations(db_session: AsyncSession):
    await seed_default_locales(db_session)

    import_data = {
        "invoice.title.main": "請求書",
        "invoice.status.paid": "支払済"
    }
    count = await import_translations(db_session, "ja-JP", import_data, "invoice")
    assert count == 2

    # Export specific module
    exported = await export_translations(db_session, "ja-JP", "invoice")
    assert exported.locale_code == "ja-JP"
    assert "invoice.title.main" in exported.translations
    assert exported.translations["invoice.status.paid"] == "支払済"

    # Export all
    exported_all = await export_translations(db_session, "ja-JP")
    assert "invoice.title.main" in exported_all.translations

    # Upsert test
    import_data_updated = {
        "invoice.status.paid": "支払い完了"
    }
    await import_translations(db_session, "ja-JP", import_data_updated, "invoice")
    val = await translate(db_session, "ja-JP", "invoice.status.paid")
    assert val == "支払い完了"

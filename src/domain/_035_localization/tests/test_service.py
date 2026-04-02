"""
Tests for localization service.
"""
from datetime import date
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError, DuplicateError, NotFoundError
from src.domain._035_localization import service
from src.domain._035_localization.schemas import LocaleCreate, TranslationCreate


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
    locale = await service.create_locale(db, data)
    assert locale.id is not None
    assert locale.code == "zh-CN"


@pytest.mark.asyncio
async def test_create_locale_invalid_code_format(db: AsyncSession):
    data = LocaleCreate(
        code="ZH-cn",
        name="Chinese",
        language="zh",
        country="CN",
        date_format="%Y-%m-%d",
        number_format="#,###.##",
        currency_code="CNY"
    )
    with pytest.raises(ValidationError):
        await service.create_locale(db, data)


@pytest.mark.asyncio
async def test_create_locale_duplicate_code(db: AsyncSession):
    data = LocaleCreate(
        code="ko-KR",
        name="Korean",
        language="ko",
        country="KR",
        date_format="%Y-%m-%d",
        number_format="#,###",
        currency_code="KRW"
    )
    await service.create_locale(db, data)

    with pytest.raises(DuplicateError):
        await service.create_locale(db, data)


@pytest.mark.asyncio
async def test_list_locales(db: AsyncSession):
    await service.create_locale(db, LocaleCreate(
        code="ru-RU", name="Russian", language="ru", country="RU",
        date_format="%d.%m.%Y", number_format="# ###,##", currency_code="RUB", is_active=True
    ))
    await service.create_locale(db, LocaleCreate(
        code="th-TH", name="Thai", language="th", country="TH",
        date_format="%d/%m/%Y", number_format="#,###.##", currency_code="THB", is_active=False
    ))

    locales = await service.list_locales(db)
    assert len(locales) >= 2

    active_locales = await service.list_locales(db, is_active=True)
    assert all(l.is_active for l in active_locales)


@pytest.mark.asyncio
async def test_add_translation_success(db: AsyncSession):
    locale = await service.create_locale(db, LocaleCreate(
        code="en-GB", name="British English", language="en", country="GB",
        date_format="%d/%m/%Y", number_format="#,###.##", currency_code="GBP"
    ))

    data = TranslationCreate(
        locale_id=locale.id,
        module="core",
        key="core.greeting.hello",
        value="Hello"
    )
    trans = await service.add_translation(db, data)
    assert trans.id is not None
    assert trans.value == "Hello"


@pytest.mark.asyncio
async def test_add_translation_invalid_key_format(db: AsyncSession):
    locale = await service.create_locale(db, LocaleCreate(
        code="en-AU", name="Aus English", language="en", country="AU",
        date_format="%d/%m/%Y", number_format="#,###.##", currency_code="AUD"
    ))

    data = TranslationCreate(
        locale_id=locale.id,
        module="core",
        key="invalid_key",
        value="Hello"
    )
    with pytest.raises(ValidationError):
        await service.add_translation(db, data)


@pytest.mark.asyncio
async def test_add_translation_empty_value(db: AsyncSession):
    locale = await service.create_locale(db, LocaleCreate(
        code="en-NZ", name="NZ English", language="en", country="NZ",
        date_format="%d/%m/%Y", number_format="#,###.##", currency_code="NZD"
    ))

    data = TranslationCreate(
        locale_id=locale.id,
        module="core",
        key="core.greeting.hello",
        value=""
    )
    with pytest.raises(ValidationError):
        await service.add_translation(db, data)


@pytest.mark.asyncio
async def test_get_translations(db: AsyncSession):
    locale = await service.create_locale(db, LocaleCreate(
        code="pt-BR", name="Portuguese", language="pt", country="BR",
        date_format="%d/%m/%Y", number_format="#.###,##", currency_code="BRL"
    ))

    await service.add_translation(db, TranslationCreate(
        locale_id=locale.id, module="sales", key="sales.invoice.title", value="Fatura"
    ))
    await service.add_translation(db, TranslationCreate(
        locale_id=locale.id, module="hr", key="hr.employee.name", value="Nome do Empregado"
    ))

    trans_all = await service.get_translations(db, "pt-BR")
    assert len(trans_all) == 2

    trans_sales = await service.get_translations(db, "pt-BR", module="sales")
    assert len(trans_sales) == 1
    assert trans_sales[0].key == "sales.invoice.title"


@pytest.mark.asyncio
async def test_get_translations_by_module(db: AsyncSession):
    locale = await service.create_locale(db, LocaleCreate(
        code="pt-PT", name="Portuguese", language="pt", country="PT",
        date_format="%d/%m/%Y", number_format="#.###,##", currency_code="EUR"
    ))

    await service.add_translation(db, TranslationCreate(
        locale_id=locale.id, module="sales", key="sales.invoice.title", value="Fatura"
    ))

    trans_dict = await service.get_translations_by_module(db, "pt-PT", "sales")
    assert trans_dict == {"sales.invoice.title": "Fatura"}


@pytest.mark.asyncio
async def test_translate(db: AsyncSession):
    locale = await service.create_locale(db, LocaleCreate(
        code="nl-NL", name="Dutch", language="nl", country="NL",
        date_format="%d-%m-%Y", number_format="#.###,##", currency_code="EUR"
    ))
    await service.add_translation(db, TranslationCreate(
        locale_id=locale.id, module="core", key="core.button.save", value="Opslaan"
    ))

    # Exists
    val = await service.translate(db, "nl-NL", "core.button.save")
    assert val == "Opslaan"

    # Missing with default
    val2 = await service.translate(db, "nl-NL", "core.button.cancel", default="Cancel")
    assert val2 == "Cancel"

    # Missing without default
    val3 = await service.translate(db, "nl-NL", "core.button.delete")
    assert val3 == "core.button.delete"


@pytest.mark.asyncio
async def test_format_date(db: AsyncSession):
    await service.create_locale(db, LocaleCreate(
        code="ja-JP", name="Japanese", language="ja", country="JP",
        date_format="%Y年%m月%d日", number_format="#,###", currency_code="JPY"
    ))
    await service.create_locale(db, LocaleCreate(
        code="en-US", name="English", language="en", country="US",
        date_format="%m/%d/%Y", number_format="#,###.##", currency_code="USD"
    ))

    d = date(2025, 1, 15)

    res_ja = await service.format_date(db, "ja-JP", d)
    assert res_ja == "2025年01月15日"

    res_en = await service.format_date(db, "en-US", d)
    assert res_en == "01/15/2025"


@pytest.mark.asyncio
async def test_format_number_and_currency(db: AsyncSession):
    await service.create_locale(db, LocaleCreate(
        code="ja-JP", name="Japanese", language="ja", country="JP",
        date_format="%Y年%m月%d日", number_format="#,###", currency_code="JPY"
    ))
    await service.create_locale(db, LocaleCreate(
        code="en-US", name="English", language="en", country="US",
        date_format="%m/%d/%Y", number_format="#,###.##", currency_code="USD"
    ))

    val1 = 1234567.89

    # Number format
    res_ja_num = await service.format_number(db, "ja-JP", val1)
    assert res_ja_num == "1,234,568"  # Rounded to 0 decimals for JPY

    res_en_num = await service.format_number(db, "en-US", val1)
    assert res_en_num == "1,234,567.89"

    # Currency format
    res_ja_cur = await service.format_currency(db, "ja-JP", 100000)
    assert res_ja_cur == "¥100,000"

    res_en_cur = await service.format_currency(db, "en-US", val1)
    assert res_en_cur == "$1,234,567.89"


@pytest.mark.asyncio
async def test_export_import_translations(db: AsyncSession):
    locale = await service.create_locale(db, LocaleCreate(
        code="pl-PL", name="Polish", language="pl", country="PL",
        date_format="%d.%m.%Y", number_format="# ###,##", currency_code="PLN"
    ))

    # Import
    data_to_import = {
        "invoice.title.main": "Faktura",
        "invoice.status.paid": "Opłacona"
    }
    count = await service.import_translations(db, "pl-PL", data_to_import, "invoice")
    assert count == 2

    # Update existing via import
    data_to_import_update = {
        "invoice.title.main": "Faktura VAT",
        "invoice.status.unpaid": "Nieopłacona"
    }
    count2 = await service.import_translations(db, "pl-PL", data_to_import_update, "invoice")
    assert count2 == 2 # 1 updated, 1 new

    # Export
    export_res = await service.export_translations(db, "pl-PL", "invoice")
    assert export_res.locale_code == "pl-PL"
    assert "invoice.title.main" in export_res.translations
    assert export_res.translations["invoice.title.main"] == "Faktura VAT"
    assert export_res.translations["invoice.status.paid"] == "Opłacona"
    assert export_res.translations["invoice.status.unpaid"] == "Nieopłacona"

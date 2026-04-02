from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import DuplicateError, ValidationError
from src.domain._035_localization import service
from src.domain._035_localization.schemas import LocaleCreate, TranslationCreate

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seeded_db(db: AsyncSession):
    await service.seed_locales(db)
    return db


async def test_create_locale(db: AsyncSession):
    data = LocaleCreate(
        code="zh-CN",
        name="Chinese",
        language="zh",
        country="CN",
        date_format="%Y-%m-%d",
        number_format="#,###.##",
        currency_code="CNY",
    )
    locale = await service.create_locale(db, data)
    assert locale.id is not None
    assert locale.code == "zh-CN"


async def test_create_locale_invalid_code(db: AsyncSession):
    data = LocaleCreate(
        code="zh-cn",
        name="Chinese",
        language="zh",
        country="CN",
        date_format="%Y-%m-%d",
        number_format="#,###.##",
        currency_code="CNY",
    )
    with pytest.raises(ValidationError):
        await service.create_locale(db, data)


async def test_create_locale_duplicate(seeded_db: AsyncSession):
    data = LocaleCreate(
        code="ja-JP",
        name="Japanese",
        language="ja",
        country="JP",
        date_format="%Y-%m-%d",
        number_format="#,###",
        currency_code="JPY",
    )
    with pytest.raises(DuplicateError):
        await service.create_locale(seeded_db, data)


async def test_list_locales(seeded_db: AsyncSession):
    locales = await service.list_locales(seeded_db)
    assert len(locales) >= 2
    codes = [loc.code for loc in locales]
    assert "ja-JP" in codes
    assert "en-US" in codes


async def test_add_translation(seeded_db: AsyncSession):
    locales = await service.list_locales(seeded_db)
    ja_locale = next(loc for loc in locales if loc.code == "ja-JP")

    data = TranslationCreate(locale_id=ja_locale.id, module="test_mod", key="test.key.name", value="テスト")
    trans = await service.add_translation(seeded_db, data)
    assert trans.id is not None


async def test_add_translation_invalid_key(seeded_db: AsyncSession):
    with pytest.raises(ValidationError):
        await service.add_translation(
            seeded_db, TranslationCreate(locale_id=1, module="mod", key="invalid", value="val")
        )


async def test_add_translation_empty_value(seeded_db: AsyncSession):
    with pytest.raises(ValidationError):
        await service.add_translation(seeded_db, TranslationCreate(locale_id=1, module="mod", key="a.b.c", value=""))


async def test_get_translations(seeded_db: AsyncSession):
    locales = await service.list_locales(seeded_db)
    loc_id = next(loc.id for loc in locales if loc.code == "ja-JP")
    await service.add_translation(
        seeded_db, TranslationCreate(locale_id=loc_id, module="mod1", key="a.b.c", value="v1")
    )
    await service.add_translation(
        seeded_db, TranslationCreate(locale_id=loc_id, module="mod2", key="x.y.z", value="v2")
    )

    trans = await service.get_translations(seeded_db, "ja-JP")
    assert len(trans) == 2

    trans_filtered = await service.get_translations(seeded_db, "ja-JP", "mod1")
    assert len(trans_filtered) == 1
    assert trans_filtered[0].value == "v1"


async def test_get_translations_by_module(seeded_db: AsyncSession):
    locales = await service.list_locales(seeded_db)
    loc_id = next(loc.id for loc in locales if loc.code == "ja-JP")
    await service.add_translation(
        seeded_db, TranslationCreate(locale_id=loc_id, module="mod1", key="a.b.c", value="v1")
    )

    res = await service.get_translations_by_module(seeded_db, "ja-JP", "mod1")
    assert isinstance(res, dict)
    assert res["a.b.c"] == "v1"


async def test_translate(seeded_db: AsyncSession):
    locales = await service.list_locales(seeded_db)
    loc_id = next(loc.id for loc in locales if loc.code == "ja-JP")
    await service.add_translation(
        seeded_db, TranslationCreate(locale_id=loc_id, module="mod", key="test.msg.hello", value="こんにちは")
    )

    val = await service.translate(seeded_db, "ja-JP", "test.msg.hello")
    assert val == "こんにちは"

    val_missing = await service.translate(seeded_db, "ja-JP", "test.msg.bye", "さようなら")
    assert val_missing == "さようなら"

    val_no_default = await service.translate(seeded_db, "ja-JP", "test.msg.bye")
    assert val_no_default == "test.msg.bye"


async def test_format_date(seeded_db: AsyncSession):
    d = date(2025, 1, 15)
    formatted_ja = await service.format_date(seeded_db, "ja-JP", d)
    assert formatted_ja == "2025年01月15日"

    formatted_en = await service.format_date(seeded_db, "en-US", d)
    assert formatted_en == "01/15/2025"


async def test_format_number(seeded_db: AsyncSession):
    val = 1234567.89
    formatted_ja = await service.format_number(seeded_db, "ja-JP", val)
    assert formatted_ja == "1,234,567"

    formatted_en = await service.format_number(seeded_db, "en-US", val)
    assert formatted_en == "1,234,567.89"


async def test_format_currency(seeded_db: AsyncSession):
    val = 100000.5
    formatted_ja = await service.format_currency(seeded_db, "ja-JP", val)
    assert formatted_ja == "¥100,000"

    formatted_en = await service.format_currency(seeded_db, "en-US", val)
    assert formatted_en == "$100,000.50"


async def test_export_translations(seeded_db: AsyncSession):
    locales = await service.list_locales(seeded_db)
    loc_id = next(loc.id for loc in locales if loc.code == "ja-JP")
    await service.add_translation(
        seeded_db, TranslationCreate(locale_id=loc_id, module="inv", key="inv.title.main", value="請求書")
    )

    export_res = await service.export_translations(seeded_db, "ja-JP", "inv")
    assert export_res.locale_code == "ja-JP"
    assert export_res.translations["inv.title.main"] == "請求書"


async def test_import_translations(seeded_db: AsyncSession):
    data = {"inv.title.main": "請求書", "inv.btn.save": "保存"}
    count = await service.import_translations(seeded_db, "ja-JP", data, "inv")
    assert count == 2

    # Upsert test
    data_update = {"inv.title.main": "新しい請求書"}
    count_update = await service.import_translations(seeded_db, "ja-JP", data_update, "inv")
    assert count_update == 1

    val = await service.translate(seeded_db, "ja-JP", "inv.title.main")
    assert val == "新しい請求書"

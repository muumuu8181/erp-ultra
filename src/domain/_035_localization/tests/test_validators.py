import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.errors import ValidationError, DuplicateError
from src.domain._035_localization.validators import validate_locale_create, validate_translation_create
from src.domain._035_localization.schemas import LocaleCreate, TranslationCreate
from src.domain._035_localization.models import Locale, Translation

pytestmark = pytest.mark.asyncio


async def test_locale_code_format(db_session: AsyncSession):
    # Pass
    data = LocaleCreate(
        code="ja-JP", name="Japanese", language="ja", country="JP",
        date_format="%Y", number_format="#", currency_code="JPY"
    )
    await validate_locale_create(db_session, data)

    # Fail
    invalid_codes = ["japanese", "JA-jp", "jJP", "ja_JP"]
    for code in invalid_codes:
        data.code = code
        with pytest.raises(ValidationError):
            await validate_locale_create(db_session, data)


async def test_locale_currency_code_format(db_session: AsyncSession):
    # Pass
    data = LocaleCreate(
        code="ja-JP", name="Japanese", language="ja", country="JP",
        date_format="%Y", number_format="#", currency_code="JPY"
    )
    await validate_locale_create(db_session, data)

    # Fail
    invalid_codes = ["jp", "JP", "Jpy", "123"]
    for code in invalid_codes:
        data.currency_code = code
        with pytest.raises(ValidationError):
            await validate_locale_create(db_session, data)


async def test_locale_duplicate_code(db_session: AsyncSession):
    locale = Locale(
        code="ja-JP", name="Japanese", language="ja", country="JP",
        date_format="%Y", number_format="#", currency_code="JPY"
    )
    db_session.add(locale)
    await db_session.commit()

    data = LocaleCreate(
        code="ja-JP", name="Another", language="ja", country="JP",
        date_format="%Y", number_format="#", currency_code="JPY"
    )
    with pytest.raises(DuplicateError):
        await validate_locale_create(db_session, data)


async def test_translation_key_format(db_session: AsyncSession):
    # Pass
    data = TranslationCreate(locale_id=1, module="invoice", key="invoice.title.main", value="Test")
    await validate_translation_create(db_session, data)

    # Fail
    invalid_keys = ["Invoice", "invoice.title", "INV.TITLE.MAIN", "invoice.title.main.sub"]
    for key in invalid_keys:
        data.key = key
        with pytest.raises(ValidationError):
            await validate_translation_create(db_session, data)


async def test_translation_value_not_empty(db_session: AsyncSession):
    data = TranslationCreate(locale_id=1, module="invoice", key="invoice.title.main", value="")
    with pytest.raises(ValidationError):
        await validate_translation_create(db_session, data)

    data.value = "   "
    with pytest.raises(ValidationError):
        await validate_translation_create(db_session, data)


async def test_translation_duplicate(db_session: AsyncSession):
    trans = Translation(locale_id=1, module="invoice", key="invoice.title.main", value="Original")
    db_session.add(trans)
    await db_session.commit()

    data = TranslationCreate(locale_id=1, module="invoice", key="invoice.title.main", value="New")
    with pytest.raises(DuplicateError):
        await validate_translation_create(db_session, data)

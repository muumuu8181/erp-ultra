import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain._035_localization.models import Locale, Translation


@pytest.mark.asyncio
async def test_locale_model(db: AsyncSession):
    # test table creation and insert
    locale = Locale(
        code="fr-FR",
        name="French",
        language="fr",
        country="FR",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db.add(locale)
    await db.commit()
    await db.refresh(locale)

    assert locale.id is not None
    assert locale.code == "fr-FR"
    assert locale.is_active is True

    # test unique code constraint
    locale2 = Locale(
        code="fr-FR",
        name="French 2",
        language="fr",
        country="FR",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db.add(locale2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


@pytest.mark.asyncio
async def test_translation_model(db: AsyncSession):
    # setup locale
    locale = Locale(
        code="de-DE",
        name="German",
        language="de",
        country="DE",
        date_format="%d.%m.%Y",
        number_format="#.###,##",
        currency_code="EUR"
    )
    db.add(locale)
    await db.commit()
    await db.refresh(locale)

    # test translation creation with FK
    translation = Translation(
        locale_id=locale.id,
        module="test_module",
        key="test.key",
        value="Test Value"
    )
    db.add(translation)
    await db.commit()
    await db.refresh(translation)

    assert translation.id is not None
    assert translation.locale_id == locale.id

    # test unique constraint on (locale_id, module, key)
    translation2 = Translation(
        locale_id=locale.id,
        module="test_module",
        key="test.key",
        value="Another Value"
    )
    db.add(translation2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

    # Enum/index verification - we check if indexes are created
    # using inspector synchronously by running on the sync engine in real tests,
    # but here we can just verify the model configuration directly
    mapper = inspect(Translation)
    assert mapper.columns.locale_id.index is True
    assert mapper.columns.module.index is True

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.domain._035_localization.models import Locale, Translation

pytestmark = pytest.mark.asyncio

async def test_locale_model(db_session: AsyncSession):
    locale = Locale(
        code="fr-FR",
        name="Français",
        language="fr",
        country="FR",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db_session.add(locale)
    await db_session.commit()
    await db_session.refresh(locale)

    assert locale.id is not None
    assert locale.code == "fr-FR"

async def test_locale_code_unique(db_session: AsyncSession):
    locale1 = Locale(
        code="es-ES",
        name="Español",
        language="es",
        country="ES",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db_session.add(locale1)
    await db_session.commit()

    locale2 = Locale(
        code="es-ES",
        name="Spanish",
        language="es",
        country="ES",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db_session.add(locale2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

async def test_translation_model(db_session: AsyncSession):
    locale = Locale(
        code="de-DE",
        name="Deutsch",
        language="de",
        country="DE",
        date_format="%d.%m.%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db_session.add(locale)
    await db_session.commit()
    await db_session.refresh(locale)

    translation = Translation(
        locale_id=locale.id,
        module="sales",
        key="sales.order.title",
        value="Kundenauftrag"
    )
    db_session.add(translation)
    await db_session.commit()
    await db_session.refresh(translation)

    assert translation.id is not None
    assert translation.value == "Kundenauftrag"
    assert translation.locale_id == locale.id

async def test_translation_unique_constraint(db_session: AsyncSession):
    locale = Locale(
        code="it-IT",
        name="Italiano",
        language="it",
        country="IT",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db_session.add(locale)
    await db_session.commit()
    await db_session.refresh(locale)

    trans1 = Translation(locale_id=locale.id, module="test", key="test.key", value="Val 1")
    db_session.add(trans1)
    await db_session.commit()

    trans2 = Translation(locale_id=locale.id, module="test", key="test.key", value="Val 2")
    db_session.add(trans2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

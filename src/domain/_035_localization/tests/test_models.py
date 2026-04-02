import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain._035_localization.models import Locale, Translation

pytestmark = pytest.mark.asyncio


async def test_locale_model_creation(db_session: AsyncSession):
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

    result = await db_session.execute(select(Locale).filter(Locale.code == "fr-FR"))
    fetched = result.scalars().first()
    assert fetched is not None
    assert fetched.name == "Français"


async def test_locale_model_unique_code(db_session: AsyncSession):
    locale1 = Locale(
        code="it-IT",
        name="Italiano",
        language="it",
        country="IT",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    locale2 = Locale(
        code="it-IT",
        name="Italiano 2",
        language="it",
        country="IT",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db_session.add(locale1)
    await db_session.commit()

    db_session.add(locale2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_translation_model_creation(db_session: AsyncSession):
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

    translation = Translation(
        locale_id=locale.id,
        module="invoice",
        key="invoice.title.main",
        value="Rechnung"
    )
    db_session.add(translation)
    await db_session.commit()

    result = await db_session.execute(select(Translation).filter(Translation.key == "invoice.title.main"))
    fetched = result.scalars().first()
    assert fetched is not None
    assert fetched.value == "Rechnung"


async def test_translation_unique_constraint(db_session: AsyncSession):
    locale = Locale(
        code="es-ES",
        name="Español",
        language="es",
        country="ES",
        date_format="%d/%m/%Y",
        number_format="#,###.##",
        currency_code="EUR"
    )
    db_session.add(locale)
    await db_session.commit()

    trans1 = Translation(
        locale_id=locale.id,
        module="common",
        key="common.button.save",
        value="Guardar"
    )
    trans2 = Translation(
        locale_id=locale.id,
        module="common",
        key="common.button.save",
        value="Save"
    )

    db_session.add(trans1)
    await db_session.commit()

    db_session.add(trans2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

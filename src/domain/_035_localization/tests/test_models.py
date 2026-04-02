"""
Tests for localization models.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.domain._035_localization.models import Locale, Translation


@pytest.mark.asyncio
async def test_locale_table_creation(db: AsyncSession):
    locale = Locale(
        code="fr-FR",
        name="Français",
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


@pytest.mark.asyncio
async def test_locale_unique_code(db: AsyncSession):
    locale1 = Locale(
        code="it-IT",
        name="Italiano",
        language="it",
        country="IT",
        date_format="%d/%m/%Y",
        number_format="#.###,##",
        currency_code="EUR"
    )
    db.add(locale1)
    await db.commit()

    locale2 = Locale(
        code="it-IT",
        name="Italian",
        language="en",
        country="IT",
        date_format="%d/%m/%Y",
        number_format="#.###,##",
        currency_code="EUR"
    )
    db.add(locale2)
    with pytest.raises(IntegrityError):
        await db.commit()

    await db.rollback()


@pytest.mark.asyncio
async def test_translation_table_creation_and_fk(db: AsyncSession):
    locale = Locale(
        code="de-DE",
        name="Deutsch",
        language="de",
        country="DE",
        date_format="%d.%m.%Y",
        number_format="#.###,##",
        currency_code="EUR"
    )
    db.add(locale)
    await db.commit()
    await db.refresh(locale)

    trans = Translation(
        locale_id=locale.id,
        module="core",
        key="core.greeting.hello",
        value="Hallo"
    )
    db.add(trans)
    await db.commit()
    await db.refresh(trans)

    assert trans.id is not None
    assert trans.locale_id == locale.id


@pytest.mark.asyncio
async def test_translation_unique_constraint(db: AsyncSession):
    locale = Locale(
        code="es-ES",
        name="Español",
        language="es",
        country="ES",
        date_format="%d/%m/%Y",
        number_format="#.###,##",
        currency_code="EUR"
    )
    db.add(locale)
    await db.commit()
    await db.refresh(locale)

    trans1 = Translation(
        locale_id=locale.id,
        module="invoice",
        key="invoice.title.main",
        value="Factura"
    )
    db.add(trans1)
    await db.commit()

    trans2 = Translation(
        locale_id=locale.id,
        module="invoice",
        key="invoice.title.main",
        value="Factura de Venta"
    )
    db.add(trans2)
    with pytest.raises(IntegrityError):
        await db.commit()

    await db.rollback()

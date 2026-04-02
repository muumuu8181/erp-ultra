import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain._035_localization.models import Locale, Translation

pytestmark = pytest.mark.asyncio


async def test_locale_model(db: AsyncSession):
    locale = Locale(
        code="fr-FR",
        name="Français",
        language="fr",
        country="FR",
        date_format="%d/%m/%Y",
        number_format="# ###,##",
        currency_code="EUR",
    )
    db.add(locale)
    await db.commit()
    await db.refresh(locale)

    assert locale.id is not None
    assert locale.code == "fr-FR"


async def test_locale_code_unique(db: AsyncSession):
    l1 = Locale(
        code="de-DE",
        name="Deutsch",
        language="de",
        country="DE",
        date_format="%d.%m.%Y",
        number_format="#.###,##",
        currency_code="EUR",
    )
    db.add(l1)
    await db.commit()

    l2 = Locale(
        code="de-DE",
        name="German",
        language="de",
        country="DE",
        date_format="%d.%m.%Y",
        number_format="#.###,##",
        currency_code="EUR",
    )
    db.add(l2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()


async def test_translation_model(db: AsyncSession):
    locale = Locale(
        code="it-IT",
        name="Italiano",
        language="it",
        country="IT",
        date_format="%d/%m/%Y",
        number_format="#.###,##",
        currency_code="EUR",
    )
    db.add(locale)
    await db.commit()

    trans = Translation(locale_id=locale.id, module="invoice", key="invoice.title.main", value="Fattura")
    db.add(trans)
    await db.commit()

    assert trans.id is not None
    assert trans.locale_id == locale.id


async def test_translation_unique_constraint(db: AsyncSession):
    locale = Locale(
        code="es-ES",
        name="Español",
        language="es",
        country="ES",
        date_format="%d/%m/%Y",
        number_format="#.###,##",
        currency_code="EUR",
    )
    db.add(locale)
    await db.commit()

    t1 = Translation(locale_id=locale.id, module="sales", key="sales.order", value="Pedido")
    db.add(t1)
    await db.commit()

    t2 = Translation(locale_id=locale.id, module="sales", key="sales.order", value="Orden")
    db.add(t2)
    with pytest.raises(IntegrityError):
        await db.commit()
    await db.rollback()

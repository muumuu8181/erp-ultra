import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain._023_address.models import Address

@pytest.mark.asyncio
async def test_address_model_creation(db_session: AsyncSession) -> None:
    """Test that an address can be created and saved to the database."""
    address = Address(
        postal_code="123-4567",
        prefecture="Tokyo",
        city="Shibuya-ku",
        street="1-2-3 Dogenzaka",
        building="Shibuya Mark City 22F"
    )

    db_session.add(address)
    await db_session.commit()
    await db_session.refresh(address)

    assert address.id is not None
    assert address.postal_code == "123-4567"
    assert address.prefecture == "Tokyo"
    assert address.city == "Shibuya-ku"
    assert address.street == "1-2-3 Dogenzaka"
    assert address.building == "Shibuya Mark City 22F"
    assert address.created_at is not None
    assert address.updated_at is not None

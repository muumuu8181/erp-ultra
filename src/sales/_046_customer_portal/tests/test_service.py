import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext # type: ignore

from shared.errors import ValidationError, DuplicateError, NotFoundError
from src.sales._046_customer_portal import service
from src.sales._046_customer_portal.schemas import PortalRegistration, PortalLogin

@pytest.mark.asyncio
async def test_register_success(db: AsyncSession):
    data = PortalRegistration(
        customer_code="CUST001",
        username="newuser",
        email="new@example.com",
        password="Valid1Pass"
    )
    user = await service.register(db, data)
    assert user.id is not None
    assert user.username == "newuser"

@pytest.mark.asyncio
async def test_register_duplicate_email(db: AsyncSession):
    data = PortalRegistration(
        customer_code="CUST001",
        username="user1",
        email="dup@example.com",
        password="Valid1Pass"
    )
    await service.register(db, data)

    data2 = PortalRegistration(
        customer_code="CUST002",
        username="user2",
        email="dup@example.com",
        password="Valid1Pass"
    )
    with pytest.raises(DuplicateError):
        await service.register(db, data2)

@pytest.mark.asyncio
async def test_register_weak_password(db: AsyncSession):
    data = PortalRegistration(
        customer_code="CUST001",
        username="user1",
        email="test@example.com",
        password="weak"
    )
    with pytest.raises(ValidationError):
        await service.register(db, data)

@pytest.mark.asyncio
async def test_login_success(db: AsyncSession):
    reg_data = PortalRegistration(
        customer_code="CUST001",
        username="loginuser",
        email="login@example.com",
        password="Valid1Pass"
    )
    await service.register(db, reg_data)

    login_data = PortalLogin(username="loginuser", password="Valid1Pass")
    session = await service.login(db, login_data, "127.0.0.1")

    assert session.token is not None

    # Refresh session to check user relation
    await db.refresh(session, ['user'])
    assert session.user.last_login is not None

@pytest.mark.asyncio
async def test_login_wrong_password(db: AsyncSession):
    reg_data = PortalRegistration(
        customer_code="CUST001",
        username="loginuser2",
        email="login2@example.com",
        password="Valid1Pass"
    )
    await service.register(db, reg_data)

    login_data = PortalLogin(username="loginuser2", password="Wrong1Pass")
    with pytest.raises(ValidationError):
        await service.login(db, login_data, "127.0.0.1")

@pytest.mark.asyncio
async def test_get_dashboard(db: AsyncSession):
    reg_data = PortalRegistration(
        customer_code="CUST001",
        username="dashuser",
        email="dash@example.com",
        password="Valid1Pass"
    )
    user = await service.register(db, reg_data)

    dash = await service.get_dashboard(db, user.id)
    assert dash.customer_code == "CUST001"

@pytest.mark.asyncio
async def test_get_order_history(db: AsyncSession):
    reg_data = PortalRegistration(
        customer_code="CUST001",
        username="orderuser",
        email="order@example.com",
        password="Valid1Pass"
    )
    user = await service.register(db, reg_data)

    history = await service.get_order_history(db, user.id, 1, 10)
    assert history.total_count == 0

@pytest.mark.asyncio
async def test_get_invoice_history(db: AsyncSession):
    reg_data = PortalRegistration(
        customer_code="CUST001",
        username="invuser",
        email="inv@example.com",
        password="Valid1Pass"
    )
    user = await service.register(db, reg_data)

    history = await service.get_invoice_history(db, user.id, 1, 10)
    assert history.total == 0

@pytest.mark.asyncio
async def test_change_password_success(db: AsyncSession):
    reg_data = PortalRegistration(
        customer_code="CUST001",
        username="pwuser",
        email="pw@example.com",
        password="Old1Pass"
    )
    user = await service.register(db, reg_data)

    success = await service.change_password(db, user.id, "Old1Pass", "New1Pass")
    assert success is True

@pytest.mark.asyncio
async def test_change_password_wrong_current(db: AsyncSession):
    reg_data = PortalRegistration(
        customer_code="CUST001",
        username="pwuser2",
        email="pw2@example.com",
        password="Old1Pass"
    )
    user = await service.register(db, reg_data)

    with pytest.raises(ValidationError):
        await service.change_password(db, user.id, "Wrong1Pass", "New1Pass")

@pytest.mark.asyncio
async def test_reset_password_request(db: AsyncSession):
    reg_data = PortalRegistration(
        customer_code="CUST001",
        username="resetuser",
        email="reset@example.com",
        password="Valid1Pass"
    )
    await service.register(db, reg_data)

    token = await service.reset_password_request(db, "reset@example.com")
    assert isinstance(token, str)

@pytest.mark.asyncio
async def test_reset_password_request_unknown(db: AsyncSession):
    with pytest.raises(NotFoundError):
        await service.reset_password_request(db, "unknown@example.com")

"""
Tests for Contract validators.
"""
from datetime import date
from decimal import Decimal
import pytest

from shared.errors import ValidationError
from src.sales._048_contract.schemas import ContractCreate, ContractUpdate, ContractStatus
from src.sales._048_contract.validators import (
    validate_contract_dates,
    validate_contract_create,
    validate_contract_update,
)


def test_validate_contract_dates_valid():
    validate_contract_dates(date(2023, 1, 1), date(2023, 12, 31))
    validate_contract_dates(date(2023, 1, 1), date(2023, 1, 1))


def test_validate_contract_dates_invalid():
    with pytest.raises(ValidationError, match="End date cannot be before start date"):
        validate_contract_dates(date(2023, 12, 31), date(2023, 1, 1))


def test_validate_contract_create_valid():
    data = ContractCreate(
        contract_number="CONT-001",
        customer_id=1,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        total_value=Decimal("1000.00"),
    )
    validate_contract_create(data)


def test_validate_contract_create_invalid_value():
    data = ContractCreate(
        contract_number="CONT-001",
        customer_id=1,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        total_value=Decimal("-10.00"),
    )
    with pytest.raises(ValidationError, match="Total value cannot be negative"):
        validate_contract_create(data)


def test_validate_contract_update_valid():
    data = ContractUpdate(
        end_date=date(2024, 12, 31),
        total_value=Decimal("2000.00"),
    )
    validate_contract_update(data, current_start=date(2023, 1, 1), current_end=date(2023, 12, 31))


def test_validate_contract_update_invalid_dates():
    data = ContractUpdate(end_date=date(2022, 12, 31))
    with pytest.raises(ValidationError, match="End date cannot be before start date"):
        validate_contract_update(data, current_start=date(2023, 1, 1), current_end=date(2023, 12, 31))


def test_validate_contract_update_invalid_value():
    data = ContractUpdate(total_value=Decimal("-50.00"))
    with pytest.raises(ValidationError, match="Total value cannot be negative"):
        validate_contract_update(data, current_start=date(2023, 1, 1), current_end=date(2023, 12, 31))

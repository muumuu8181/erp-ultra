"""
Business rule validation for Contract Management.
"""
from datetime import date

from shared.errors import ValidationError
from src.sales._048_contract.schemas import ContractCreate, ContractUpdate


def validate_contract_dates(start_date: date | None, end_date: date | None) -> None:
    """
    Ensure that the start date is before or equal to the end date.

    Raises:
        ValidationError: If start_date is after end_date.
    """
    if start_date and end_date:
        if start_date > end_date:
            raise ValidationError("End date cannot be before start date", field="end_date")


def validate_contract_create(data: ContractCreate) -> None:
    """
    Validate business rules for creating a contract.
    """
    validate_contract_dates(data.start_date, data.end_date)

    if data.total_value < 0:
        raise ValidationError("Total value cannot be negative", field="total_value")


def validate_contract_update(data: ContractUpdate, current_start: date, current_end: date) -> None:
    """
    Validate business rules for updating a contract.
    """
    start = data.start_date if data.start_date else current_start
    end = data.end_date if data.end_date else current_end

    validate_contract_dates(start, end)

    if data.total_value is not None and data.total_value < 0:
        raise ValidationError("Total value cannot be negative", field="total_value")

import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError
from sales._042_commission.schemas import CommissionCreate, CommissionUpdate

def test_commission_create_schema_valid():
    data = CommissionCreate(
        salesperson_id=1,
        sales_order_id=2,
        commission_rate=Decimal("10.5"),
        amount=Decimal("100.00"),
        calculation_date=date(2023, 1, 1)
    )
    assert data.salesperson_id == 1
    assert data.amount == Decimal("100.00")
    assert data.currency == "JPY"

def test_commission_create_schema_missing_fields():
    with pytest.raises(ValidationError):
        CommissionCreate(
            salesperson_id=1,
            # missing required fields
        )

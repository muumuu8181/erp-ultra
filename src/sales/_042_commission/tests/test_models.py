import pytest
from datetime import date
from decimal import Decimal
from sales._042_commission.models import Commission

def test_commission_model():
    commission = Commission(
        salesperson_id=1,
        sales_order_id=2,
        commission_rate=Decimal("10.5"),
        amount=Decimal("100.00"),
        currency="JPY",
        status="active",
        calculation_date=date(2023, 1, 1)
    )
    assert commission.salesperson_id == 1
    assert commission.sales_order_id == 2
    assert commission.commission_rate == Decimal("10.5")
    assert commission.amount == Decimal("100.00")

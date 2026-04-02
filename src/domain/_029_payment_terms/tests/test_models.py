"""
Tests for Payment Terms models.
"""
from src.domain._029_payment_terms.models import PaymentTerm

def test_payment_term_model_init():
    """Test initializing a PaymentTerm model."""
    term = PaymentTerm(
        code="NET30",
        name="Net 30 Days",
        description="Payment due in 30 days",
        days=30,
        is_active=True
    )

    assert term.code == "NET30"
    assert term.name == "Net 30 Days"
    assert term.description == "Payment due in 30 days"
    assert term.days == 30
    assert term.is_active is True

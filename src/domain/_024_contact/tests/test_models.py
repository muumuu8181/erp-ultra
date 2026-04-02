from domain._024_contact.models import Contact

def test_contact_model_initialization():
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+1234567890",
        department="Sales"
    )
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.email == "john@example.com"
    assert contact.phone == "+1234567890"
    assert contact.department == "Sales"
        # In SQLAlchemy models without default instantiated value, it might be None before flush
        # However boolean with default might be handled DB-side

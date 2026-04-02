from src.domain._030_attachment.models import Attachment

def test_attachment_model_instantiation():
    """Test that the Attachment model can be instantiated with valid data."""
    attachment = Attachment(code="TEST-01", name="test_file.txt")
    assert attachment.code == "TEST-01"
    assert attachment.name == "test_file.txt"

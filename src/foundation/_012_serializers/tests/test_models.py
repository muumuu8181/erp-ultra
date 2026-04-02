from src.foundation._012_serializers import models

def test_models_import():
    """Verify models file can be imported and contains expected docs."""
    assert models.__doc__ is not None
    assert "No database models" in models.__doc__

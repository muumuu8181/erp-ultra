from typing import Any

from pydantic import BaseModel

from shared.errors import ValidationError
from .schemas import ExportFormat


def validate_serialize_data(data: Any, format: str) -> None:
    """Validate that data can be serialized to the target format.

    Rules:
    - CSV: data must be a list of dicts (or empty list)
    - JSON: any JSON-serializable data
    - XML: must be a dict or list

    Args:
        data: The data to validate.
        format: Target format string ("csv", "json", "xml").
    Raises:
        ValidationError: If data is incompatible with the format.
    """
    if format == ExportFormat.CSV.value:
        if not isinstance(data, list):
            raise ValidationError("CSV data must be a list.", field="data")
        if data and not all(isinstance(item, dict) for item in data):
            raise ValidationError("CSV data must be a list of dicts.", field="data")

    elif format == ExportFormat.XML.value:
        if isinstance(data, BaseModel):
            pass
        elif not isinstance(data, (dict, list)):
            raise ValidationError("XML data must be a dict, list, or Pydantic model.", field="data")

    elif format == ExportFormat.JSON.value:
        pass # JSON serialization handles its own errors
    else:
        raise ValidationError(f"Unsupported format: {format}", field="format")


def validate_deserialize_content(content: str, format: str) -> None:
    """Validate that the content string is non-empty and plausibly valid.

    Args:
        content: The string content to validate.
        format: Source format string.
    Raises:
        ValidationError: If content is empty or format is unsupported.
    """
    if not isinstance(content, str):
        raise ValidationError("Content must be a string.", field="content")

    if not content.strip():
        raise ValidationError("Content cannot be empty.", field="content")

    if format not in [ExportFormat.CSV.value, ExportFormat.JSON.value, ExportFormat.XML.value]:
        raise ValidationError(f"Unsupported format: {format}", field="format")


def validate_flatten_data(data: Any, max_depth: int) -> None:
    """Validate that data can be flattened within max_depth.

    Args:
        data: The data to validate.
        max_depth: Maximum allowed nesting depth.
    Raises:
        ValidationError: If data exceeds max_depth or is not a dict/model.
    """
    if max_depth < 0:
        raise ValidationError("max_depth must be non-negative.", field="max_depth")

    if isinstance(data, BaseModel):
        data = data.model_dump()

    if not isinstance(data, dict):
        raise ValidationError("Flattening requires a dict or Pydantic model.", field="data")

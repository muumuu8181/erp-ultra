from enum import Enum
from typing import Any, Optional

from pydantic import Field

from shared.types import BaseSchema


class ExportFormat(str, Enum):
    """Supported export/import formats."""

    CSV = "csv"
    JSON = "json"
    XML = "xml"


class SerializeRequest(BaseSchema):
    """Request to serialize data to a specific format."""

    data: Any = Field(
        ..., description="Data to serialize (list of dicts, dict, or Pydantic model)"
    )
    format: ExportFormat = Field(..., description="Target format")
    include_bom: bool = Field(
        True, description="Include BOM for CSV (Excel compatibility)"
    )
    pretty: bool = Field(False, description="Pretty-print output (JSON/XML)")
    root_element: str = Field("root", description="Root element name for XML")
    item_element: str = Field("item", description="Item element name for XML lists")


class DeserializeRequest(BaseSchema):
    """Request to deserialize data from a specific format."""

    content: str = Field(..., description="String content to deserialize")
    format: ExportFormat = Field(..., description="Source format")
    schema_name: Optional[str] = Field(
        None, description="Optional Pydantic schema name for typed deserialization"
    )


class FlattenRequest(BaseSchema):
    """Request to flatten a nested dict/Pydantic model."""

    data: Any = Field(..., description="Nested data structure to flatten")
    separator: str = Field(".", description="Separator for flattened keys (default: dot)")
    max_depth: int = Field(10, description="Maximum nesting depth to flatten")


class SerializeResponse(BaseSchema):
    """Response from a serialization operation."""

    format: str = Field(..., description="Output format")
    content: str = Field(..., description="Serialized string content")
    content_type: str = Field(..., description="MIME type of the content")
    row_count: Optional[int] = Field(
        None, description="Number of rows (for CSV/tabular data)"
    )


class DeserializeResponse(BaseSchema):
    """Response from a deserialization operation."""

    format: str = Field(..., description="Input format")
    data: Any = Field(..., description="Deserialized data structure")
    row_count: Optional[int] = Field(
        None, description="Number of rows (for CSV/tabular data)"
    )


class FlattenResponse(BaseSchema):
    """Response from a flatten operation."""

    original_keys: int = Field(
        ..., description="Number of keys in original structure"
    )
    flattened_keys: int = Field(
        ..., description="Number of keys after flattening"
    )
    data: dict[str, Any] = Field(
        ..., description="Flattened dictionary with dot-notation keys"
    )

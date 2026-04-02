"""
Serializers / Data Export module.
A pure utility module providing serialization and deserialization services
for converting data between formats (CSV, JSON, XML) and flattening nested structures.
"""

from .service import (
    to_csv,
    to_json,
    to_xml,
    to_flat_dict,
    from_csv,
    from_json,
    from_xml,
    CustomJSONEncoder,
)
from .schemas import (
    ExportFormat,
    SerializeRequest,
    DeserializeRequest,
    FlattenRequest,
    SerializeResponse,
    DeserializeResponse,
    FlattenResponse,
)

__all__ = [
    "to_csv",
    "to_json",
    "to_xml",
    "to_flat_dict",
    "from_csv",
    "from_json",
    "from_xml",
    "CustomJSONEncoder",
    "ExportFormat",
    "SerializeRequest",
    "DeserializeRequest",
    "FlattenRequest",
    "SerializeResponse",
    "DeserializeResponse",
    "FlattenResponse",
]

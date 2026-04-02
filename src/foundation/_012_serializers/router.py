from fastapi import APIRouter

from .schemas import (
    SerializeRequest,
    SerializeResponse,
    DeserializeRequest,
    DeserializeResponse,
    FlattenRequest,
    FlattenResponse,
    ExportFormat,
)
from .service import (
    to_csv,
    to_json,
    to_xml,
    to_flat_dict,
    from_csv,
    from_json,
    from_xml,
)
from .validators import (
    validate_serialize_data,
    validate_deserialize_content,
    validate_flatten_data,
)

router = APIRouter(prefix="/api/v1/serialize", tags=["serializers"])


@router.post("/csv", response_model=SerializeResponse)
async def serialize_to_csv(request: SerializeRequest) -> SerializeResponse:
    """Serialize data to CSV format."""
    validate_serialize_data(request.data, ExportFormat.CSV.value)

    content = to_csv(request.data, request.include_bom)

    return SerializeResponse(
        format=ExportFormat.CSV.value,
        content=content,
        content_type="text/csv",
        row_count=len(request.data) if isinstance(request.data, list) else None,
    )


@router.post("/json", response_model=SerializeResponse)
async def serialize_to_json(request: SerializeRequest) -> SerializeResponse:
    """Serialize data to JSON format."""
    validate_serialize_data(request.data, ExportFormat.JSON.value)

    content = to_json(request.data, request.pretty)

    return SerializeResponse(
        format=ExportFormat.JSON.value,
        content=content,
        content_type="application/json",
    )


@router.post("/xml", response_model=SerializeResponse)
async def serialize_to_xml(request: SerializeRequest) -> SerializeResponse:
    """Serialize data to XML format."""
    validate_serialize_data(request.data, ExportFormat.XML.value)

    content = to_xml(request.data, request.root_element, request.item_element, request.pretty)

    return SerializeResponse(
        format=ExportFormat.XML.value,
        content=content,
        content_type="application/xml",
    )


@router.post("/deserialize/csv", response_model=DeserializeResponse)
async def deserialize_from_csv(request: DeserializeRequest) -> DeserializeResponse:
    """Deserialize CSV content to data."""
    validate_deserialize_content(request.content, ExportFormat.CSV.value)

    data = from_csv(request.content)

    return DeserializeResponse(
        format=ExportFormat.CSV.value,
        data=data,
        row_count=len(data) if isinstance(data, list) else None,
    )


@router.post("/deserialize/json", response_model=DeserializeResponse)
async def deserialize_from_json(request: DeserializeRequest) -> DeserializeResponse:
    """Deserialize JSON content to data."""
    validate_deserialize_content(request.content, ExportFormat.JSON.value)

    data = from_json(request.content)

    return DeserializeResponse(
        format=ExportFormat.JSON.value,
        data=data,
    )


@router.post("/deserialize/xml", response_model=DeserializeResponse)
async def deserialize_from_xml(request: DeserializeRequest) -> DeserializeResponse:
    """Deserialize XML content to data."""
    validate_deserialize_content(request.content, ExportFormat.XML.value)

    data = from_xml(request.content)

    return DeserializeResponse(
        format=ExportFormat.XML.value,
        data=data,
    )


@router.post("/flatten", response_model=FlattenResponse)
async def flatten_data(request: FlattenRequest) -> FlattenResponse:
    """Flatten nested data."""
    validate_flatten_data(request.data, request.max_depth)

    original_keys = len(request.data.keys()) if isinstance(request.data, dict) else 1

    flat_data = to_flat_dict(request.data, request.separator, request.max_depth)

    return FlattenResponse(
        original_keys=original_keys,
        flattened_keys=len(flat_data.keys()),
        data=flat_data,
    )

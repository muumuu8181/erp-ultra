import pytest
from pydantic import BaseModel

from src.foundation._012_serializers.validators import (
    validate_serialize_data,
    validate_deserialize_content,
    validate_flatten_data,
)
from src.foundation._012_serializers.schemas import ExportFormat
from shared.errors import ValidationError


class DummyModel(BaseModel):
    name: str


def test_validate_serialize_data_csv_valid():
    validate_serialize_data([{"a": 1}], ExportFormat.CSV.value)
    validate_serialize_data([], ExportFormat.CSV.value)


def test_validate_serialize_data_csv_invalid():
    with pytest.raises(ValidationError):
        validate_serialize_data({"a": 1}, ExportFormat.CSV.value)
    with pytest.raises(ValidationError):
        validate_serialize_data([1, 2], ExportFormat.CSV.value)


def test_validate_serialize_data_json_valid():
    validate_serialize_data({"a": 1}, ExportFormat.JSON.value)
    validate_serialize_data([1, 2], ExportFormat.JSON.value)


def test_validate_serialize_data_xml_valid():
    validate_serialize_data({"a": 1}, ExportFormat.XML.value)
    validate_serialize_data([1, 2], ExportFormat.XML.value)
    validate_serialize_data(DummyModel(name="test"), ExportFormat.XML.value)


def test_validate_serialize_data_xml_invalid():
    with pytest.raises(ValidationError):
        validate_serialize_data("string", ExportFormat.XML.value)


def test_validate_serialize_data_unsupported_format():
    with pytest.raises(ValidationError):
        validate_serialize_data({"a": 1}, "unsupported")


def test_validate_deserialize_content_valid():
    validate_deserialize_content("content", ExportFormat.CSV.value)
    validate_deserialize_content("content", ExportFormat.JSON.value)
    validate_deserialize_content("content", ExportFormat.XML.value)


def test_validate_deserialize_content_invalid():
    with pytest.raises(ValidationError):
        validate_deserialize_content("", ExportFormat.CSV.value)
    with pytest.raises(ValidationError):
        validate_deserialize_content("  ", ExportFormat.CSV.value)
    with pytest.raises(ValidationError):
        validate_deserialize_content(None, ExportFormat.CSV.value)


def test_validate_deserialize_content_unsupported_format():
    with pytest.raises(ValidationError):
        validate_deserialize_content("content", "unsupported")


def test_validate_flatten_data_valid():
    validate_flatten_data({"a": {"b": 1}}, 10)
    validate_flatten_data(DummyModel(name="test"), 10)


def test_validate_flatten_data_invalid():
    with pytest.raises(ValidationError):
        validate_flatten_data("string", 10)
    with pytest.raises(ValidationError):
        validate_flatten_data({"a": 1}, -1)

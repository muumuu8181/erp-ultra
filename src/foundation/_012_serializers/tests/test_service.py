import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

import pytest
from pydantic import BaseModel

from shared.errors import ValidationError
from src.foundation._012_serializers.service import (
    to_csv,
    to_json,
    to_flat_dict,
    from_csv,
    from_json,
    to_xml,
    from_xml,
)


class SampleEnum(Enum):
    A = "Value A"
    B = "Value B"


class SampleModel(BaseModel):
    name: str
    value: int


# --- to_csv tests ---

def test_to_csv_simple():
    data = [{"name": "Alice", "age": 30}]
    csv_str = to_csv(data, include_bom=False)
    assert csv_str == "name,age\nAlice,30\n"


def test_to_csv_bom():
    data = [{"name": "Alice", "age": 30}]
    csv_str = to_csv(data, include_bom=True)
    assert csv_str.startswith("\ufeff")
    assert csv_str == "\ufeffname,age\nAlice,30\n"


def test_to_csv_empty():
    assert to_csv([], include_bom=False) == ""
    assert to_csv([], include_bom=True) == "\ufeff"


def test_to_csv_none_values():
    data = [{"name": "Alice", "age": None}]
    csv_str = to_csv(data, include_bom=False)
    assert csv_str == "name,age\nAlice,\n"


def test_to_csv_decimal():
    data = [{"name": "Alice", "balance": Decimal("100.50")}]
    csv_str = to_csv(data, include_bom=False)
    assert csv_str == "name,balance\nAlice,100.5\n"


def test_to_csv_datetime():
    dt = datetime(2024, 1, 15, 10, 30, 0)
    data = [{"name": "Alice", "created_at": dt}]
    csv_str = to_csv(data, include_bom=False)
    assert csv_str == "name,created_at\nAlice,2024-01-15T10:30:00\n"


def test_to_csv_quotes():
    data = [{"name": 'Alice, "The Great"', "age": 30}]
    csv_str = to_csv(data, include_bom=False)
    assert csv_str == 'name,age\n"Alice, ""The Great""",30\n'


def test_to_csv_invalid():
    with pytest.raises(ValidationError):
        to_csv({"name": "Alice"})
    with pytest.raises(ValidationError):
        to_csv([1, 2, 3])


# --- to_json tests ---

def test_to_json_simple():
    data = {"key": "value"}
    json_str = to_json(data)
    assert json.loads(json_str) == data


def test_to_json_custom_types():
    data = {
        "decimal": Decimal("100.50"),
        "datetime": datetime(2024, 1, 15, 10, 30, 0),
        "date": date(2024, 1, 15),
        "enum": SampleEnum.A,
        "bytes": b"hello",
        "set": {1, 2},
    }
    json_str = to_json(data)
    parsed = json.loads(json_str)
    assert parsed["decimal"] == 100.5
    assert parsed["datetime"] == "2024-01-15T10:30:00"
    assert parsed["date"] == "2024-01-15"
    assert parsed["enum"] == "Value A"
    assert parsed["bytes"] == "aGVsbG8="  # base64 for 'hello'
    assert set(parsed["set"]) == {1, 2}


def test_to_json_pretty():
    data = {"a": 1, "b": {"c": 2}}
    json_str = to_json(data, pretty=True)
    assert "\n" in json_str
    assert "  " in json_str


def test_to_json_invalid():
    with pytest.raises(ValidationError):
        to_json(object())


# --- to_flat_dict tests ---

def test_to_flat_dict_simple():
    data = {"a": 1, "b": 2}
    assert to_flat_dict(data) == {"a": 1, "b": 2}


def test_to_flat_dict_nested():
    data = {"a": {"b": 1}}
    assert to_flat_dict(data) == {"a.b": 1}


def test_to_flat_dict_deep():
    data = {"a": {"b": {"c": 1}}}
    assert to_flat_dict(data) == {"a.b.c": 1}


def test_to_flat_dict_mixed():
    data = {"name": "test", "address": {"city": "Tokyo"}}
    assert to_flat_dict(data) == {"name": "test", "address.city": "Tokyo"}


def test_to_flat_dict_list():
    data = {"tags": [1, 2, 3]}
    assert to_flat_dict(data) == {"tags": [1, 2, 3]}


def test_to_flat_dict_empty():
    assert to_flat_dict({}) == {}


def test_to_flat_dict_custom_separator():
    data = {"a": {"b": 1}}
    assert to_flat_dict(data, separator="_") == {"a_b": 1}


def test_to_flat_dict_max_depth():
    data = {"a": {"b": {"c": 1}}}
    with pytest.raises(ValidationError):
        to_flat_dict(data, max_depth=1)


def test_to_flat_dict_pydantic():
    data = SampleModel(name="test", value=1)
    assert to_flat_dict(data) == {"name": "test", "value": 1}


# --- from_csv tests ---

def test_from_csv_simple():
    csv_str = "name,age\nAlice,30\n"
    data = from_csv(csv_str)
    assert data == [{"name": "Alice", "age": 30}]


def test_from_csv_bom():
    csv_str = "\ufeffname,age\nAlice,30\n"
    data = from_csv(csv_str)
    assert data == [{"name": "Alice", "age": 30}]


def test_from_csv_quotes():
    csv_str = 'name,age\n"Alice, Bob",30\n'
    data = from_csv(csv_str)
    assert data == [{"name": "Alice, Bob", "age": 30}]


def test_from_csv_none():
    csv_str = "name,age\nAlice,\n"
    data = from_csv(csv_str)
    assert data == [{"name": "Alice", "age": None}]


def test_from_csv_numeric():
    csv_str = "val_int,val_float,val_str\n10,10.5,010\n"
    data = from_csv(csv_str)
    assert data == [{"val_int": 10, "val_float": 10.5, "val_str": "010"}]


def test_from_csv_empty():
    with pytest.raises(ValidationError):
        from_csv("")


# --- from_json tests ---

def test_from_json_simple():
    json_str = '{"key": "value"}'
    assert from_json(json_str) == {"key": "value"}


def test_from_json_array():
    json_str = '[1, 2, 3]'
    assert from_json(json_str) == [1, 2, 3]


def test_from_json_invalid():
    with pytest.raises(ValidationError):
        from_json("{invalid}")


# --- to_xml tests ---

def test_to_xml_simple():
    data = {"name": "Alice"}
    xml_str = to_xml(data)
    assert "<root><name>Alice</name></root>" in xml_str


def test_to_xml_nested():
    data = {"person": {"name": "Alice"}}
    xml_str = to_xml(data)
    assert "<root><person><name>Alice</name></person></root>" in xml_str


def test_to_xml_list():
    data = [1, 2, 3]
    xml_str = to_xml(data)
    assert "<root><item>1</item><item>2</item><item>3</item></root>" in xml_str


def test_to_xml_none():
    data = {"field": None}
    xml_str = to_xml(data)
    assert "<root><field /></root>" in xml_str or "<root><field/></root>" in xml_str.replace(" ", "")


def test_to_xml_boolean():
    data = {"active": True, "inactive": False}
    xml_str = to_xml(data)
    assert "<active>true</active>" in xml_str
    assert "<inactive>false</inactive>" in xml_str


def test_to_xml_custom_elements():
    data = [1]
    xml_str = to_xml(data, root_element="wrapper", item_element="element")
    assert "<wrapper><element>1</element></wrapper>" in xml_str


def test_to_xml_pretty():
    data = {"a": {"b": 1}}
    xml_str = to_xml(data, pretty=True)
    assert "\n" in xml_str
    assert "  " in xml_str


# --- from_xml tests ---

def test_from_xml_simple():
    xml_str = "<root><name>Alice</name></root>"
    assert from_xml(xml_str) == {"name": "Alice"}


def test_from_xml_nested():
    xml_str = "<root><person><name>Alice</name></person></root>"
    assert from_xml(xml_str) == {"person": {"name": "Alice"}}


def test_from_xml_list():
    xml_str = "<root><item>1</item><item>2</item></root>"
    assert from_xml(xml_str) == {"item": ["1", "2"]}


def test_from_xml_empty():
    xml_str = "<root><empty/></root>"
    assert from_xml(xml_str) == {"empty": None}


def test_from_xml_attributes():
    xml_str = '<root><person id="1">Alice</person></root>'
    assert from_xml(xml_str) == {"person": {"@id": "1", "#text": "Alice"}}


def test_from_xml_invalid():
    with pytest.raises(ValidationError):
        from_xml("<root><unclosed>")

import csv
import io
import json
import defusedxml.ElementTree as ET
import xml.etree.ElementTree as standard_ET
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
import xml.dom.minidom

from pydantic import BaseModel

from shared.errors import ValidationError


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder handling special Python types.

    Handles:
    - Decimal -> float (preserve precision as much as possible)
    - datetime -> ISO 8601 string (e.g. "2024-01-15T10:30:00")
    - date -> ISO 8601 string (e.g. "2024-01-15")
    - Enum -> enum.value
    - bytes -> base64 encoded string
    - set -> list
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, bytes):
            import base64
            return base64.b64encode(obj).decode("ascii")
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


def to_csv(data: list[dict[str, Any]], include_bom: bool = True) -> str:
    """Convert a list of dicts to a CSV string.

    Features:
    - UTF-8 with optional BOM (Byte Order Mark) for Excel compatibility
    - BOM is the UTF-8 BOM: \\xef\\xbb\\xbf
    - Proper quoting: fields containing commas, quotes, or newlines are quoted
    - All fields quoted with double-quote escaping
    - Keys from the first dict become headers
    - Empty list returns empty string with BOM if include_bom
    - None values become empty strings
    - Decimal values converted to float string representation
    - datetime/date values converted to ISO 8601

    Args:
        data: List of dicts to serialize. Each dict represents a row.
        include_bom: Whether to prepend UTF-8 BOM for Excel compatibility.
    Returns:
        CSV string (with optional BOM prefix).
    Raises:
        ValidationError: If data is not a list of dicts.
    """
    if not isinstance(data, list):
        raise ValidationError("CSV data must be a list of dicts.", field="data")

    if not data:
        if include_bom:
            return "\ufeff"
        return ""

    if not all(isinstance(row, dict) for row in data):
        raise ValidationError("CSV data must be a list of dicts.", field="data")

    output = io.StringIO()
    if include_bom:
        output.write("\ufeff")

    # Get headers from the first dict
    fieldnames = list(data[0].keys())

    # We use csv.writer to have more control over the output, or DictWriter
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    writer.writeheader()

    for row in data:
        formatted_row = {}
        for key, value in row.items():
            if value is None:
                formatted_row[key] = ""
            elif isinstance(value, Decimal):
                formatted_row[key] = str(float(value))
            elif isinstance(value, (datetime, date)):
                formatted_row[key] = value.isoformat()
            elif isinstance(value, Enum):
                formatted_row[key] = str(value.value)
            else:
                formatted_row[key] = str(value)
        writer.writerow(formatted_row)

    return output.getvalue()


def to_json(data: Any, pretty: bool = False) -> str:
    """Convert structured data to JSON string with custom encoders.

    Uses CustomJSONEncoder for Decimal, datetime, date, Enum handling.

    Args:
        data: Any JSON-serializable data.
        pretty: If True, indent with 2 spaces.
    Returns:
        JSON string.
    Raises:
        ValidationError: If data cannot be serialized.
    """
    kwargs = {"cls": CustomJSONEncoder}
    if pretty:
        kwargs["indent"] = 2

    try:
        if isinstance(data, BaseModel):
            data = data.model_dump()
        return json.dumps(data, **kwargs)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Failed to serialize to JSON: {e}", field="data")


def to_flat_dict(data: Any, separator: str = ".", max_depth: int = 10) -> dict[str, Any]:
    """Flatten a nested dict or Pydantic model to a flat dict with dot-notation keys.

    Rules:
    - Nested dicts are flattened recursively
    - Pydantic models are converted to dicts first
    - Lists are preserved as-is (not flattened by index)
    - max_depth prevents infinite recursion
    - Empty dicts produce no keys
    - None values are preserved

    Args:
        data: Nested dict, Pydantic model, or any structure to flatten.
        separator: Separator string for nested keys (default ".").
        max_depth: Maximum nesting depth to flatten.
    Returns:
        Flat dictionary with dot-notation keys.
    Raises:
        ValidationError: If max_depth exceeded.
    """
    if isinstance(data, BaseModel):
        data = data.model_dump()

    if not isinstance(data, dict):
        return { "": data } if data is not None else {}

    result = {}

    def flatten(current_data: Any, current_key: str, depth: int) -> None:
        if depth > max_depth:
            raise ValidationError(f"Max depth {max_depth} exceeded", field="data")

        if isinstance(current_data, dict):
            if not current_data:
                pass # Empty dict produces no keys
            for k, v in current_data.items():
                new_key = f"{current_key}{separator}{k}" if current_key else str(k)
                flatten(v, new_key, depth + 1)
        else:
            if current_key:
                result[current_key] = current_data

    flatten(data, "", 0)
    return result


def from_csv(content: str) -> list[dict[str, Any]]:
    """Parse a CSV string into a list of dicts.

    Features:
    - Handles BOM (strips it)
    - First row is headers
    - Proper CSV quoting
    - Empty strings become None
    - Attempts numeric conversion for values that look numeric
    - Preserves leading zeros

    Args:
        content: CSV string content.
    Returns:
        List of dicts, one per row, with header keys.
    Raises:
        ValidationError: If CSV content is malformed.
    """
    if not content.strip():
        raise ValidationError("CSV content is empty", field="content")

    # Strip BOM if present
    if content.startswith("\ufeff"):
        content = content[1:]

    try:
        reader = csv.DictReader(io.StringIO(content))
        result = []
        for row in reader:
            parsed_row = {}
            for k, v in row.items():
                if v == "":
                    parsed_row[k] = None
                else:
                    # Attempt numeric conversion
                    if v.isdigit() and not (v.startswith("0") and len(v) > 1):
                        parsed_row[k] = int(v)
                    else:
                        try:
                            # Try float if it's not a leading zero string and has a dot
                            if "." in v and not (v.startswith("0") and len(v.split(".")[0]) > 1):
                                parsed_row[k] = float(v)
                            else:
                                parsed_row[k] = v
                        except ValueError:
                            parsed_row[k] = v
            result.append(parsed_row)
        return result
    except csv.Error as e:
        raise ValidationError(f"Malformed CSV: {e}", field="content")


def from_json(content: str) -> Any:
    """Parse a JSON string into typed data.

    Args:
        content: JSON string content.
    Returns:
        Parsed Python data structure.
    Raises:
        ValidationError: If JSON content is malformed.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Malformed JSON: {e}", field="content")


def _build_xml_element(tag: str, data: Any, item_element: str = "item") -> standard_ET.Element:
    elem = standard_ET.Element(tag)
    if data is None:
        pass # Empty element
    elif isinstance(data, bool):
        elem.text = "true" if data else "false"
    elif isinstance(data, dict):
        for k, v in data.items():
            child = _build_xml_element(str(k), v, item_element)
            elem.append(child)
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            child = _build_xml_element(item_element, item, item_element)
            elem.append(child)
    else:
        # Primitives
        elem.text = str(data)
    return elem


def to_xml(data: Any, root_element: str = "root", item_element: str = "item", pretty: bool = False) -> str:
    """Convert a dict or list to an XML string.

    Args:
        data: Dict or list to convert.
        root_element: Name of the root XML element.
        item_element: Name for list item wrapper elements.
        pretty: If True, indent with 2 spaces.
    Returns:
        XML string.
    Raises:
        ValidationError: If data cannot be converted to XML.
    """
    if isinstance(data, BaseModel):
        data = data.model_dump()

    try:
        root = _build_xml_element(root_element, data, item_element)
        xml_str = standard_ET.tostring(root, encoding="unicode")
        if pretty:
            parsed = xml.dom.minidom.parseString(xml_str)
            # toprettyxml adds extra newlines for text nodes if not careful, but minidom standard works okay for simple cases
            # Custom pretty print to avoid extra whitespace around text
            return parsed.toprettyxml(indent="  ")
        return xml_str
    except Exception as e:
        raise ValidationError(f"Failed to serialize to XML: {e}", field="data")


def _parse_xml_element(elem: standard_ET.Element) -> Any:
    children = list(elem)

    if not children:
        # Check attributes
        if elem.attrib:
            res = {f"@{k}": v for k, v in elem.attrib.items()}
            if elem.text and elem.text.strip():
                res["#text"] = elem.text.strip()
            return res

        if elem.text is None or not elem.text.strip():
            return None
        return elem.text.strip()

    res = {}
    if elem.attrib:
        for k, v in elem.attrib.items():
            res[f"@{k}"] = v

    # Group by tag to handle lists
    child_dict: dict[str, list[Any]] = {}
    for child in children:
        child_dict.setdefault(child.tag, []).append(_parse_xml_element(child))

    for tag, values in child_dict.items():
        if len(values) == 1:
            res[tag] = values[0]
        else:
            res[tag] = values

    if elem.text and elem.text.strip():
        res["#text"] = elem.text.strip()

    return res


def from_xml(content: str) -> dict[str, Any]:
    """Parse an XML string into a dict.

    Args:
        content: XML string content.
    Returns:
        Dictionary representation of the XML.
    Raises:
        ValidationError: If XML content is malformed.
    """
    try:
        root = ET.fromstring(content)
        # We don't include the root element in the parsed dict
        return _parse_xml_element(root)
    except ET.ParseError as e:
        raise ValidationError(f"Malformed XML: {e}", field="content")

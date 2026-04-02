# Serializers / Data Export Module

A pure utility module providing serialization and deserialization services for converting data between formats (CSV, JSON, XML) and flattening nested structures. It handles Japanese-specific needs like BOM for Excel CSV compatibility and proper Decimal/datetime encoding.

## Features

- Serialization to CSV, JSON, and XML.
- Deserialization from CSV, JSON, and XML.
- Flattening of nested dictionary or Pydantic models.
- Custom JSON encoding for Decimals, datetimes, dates, enums, etc.
- Support for Excel-compatible CSVs with BOM.

## Usage

This is a utility module with no database dependencies. See `schemas.py`, `service.py`, and `router.py` for API definitions.

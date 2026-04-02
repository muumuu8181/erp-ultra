# Unit of Measure (026)

This module handles units of measure definitions and conversions between units.

## Features
- Define units of measure with configurable decimal places
- Support unit types (count, weight, volume, length, time, area)
- Define conversion factors between units
- Automatic transitive conversions (e.g. M -> CM -> MM) using BFS

## Endpoints
- `POST /api/v1/uoms`: Create a UOM
- `GET /api/v1/uoms`: List UOMs
- `POST /api/v1/uoms/conversions`: Create a conversion factor
- `GET /api/v1/uoms/conversions`: List conversions for a UOM
- `POST /api/v1/uoms/convert`: Convert a quantity between units
- `GET /api/v1/uoms/{id}/compatible`: Get all compatible units

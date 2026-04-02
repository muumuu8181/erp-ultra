# Product Model Module

This module handles product master data management including pricing, categories, and inventory parameters.

## Structure

- `models.py`: Defines the SQLAlchemy models (`Product` and `ProductCategory`).
- `schemas.py`: Defines the Pydantic schemas for data validation.
- `validators.py`: Contains validation functions to enforce business rules.
- `service.py`: Implements CRUD operations and business logic.
- `router.py`: Provides FastAPI endpoints.

## Endpoints

See `router.py` for full details. Endpoints are mounted at `/api/v1/products`.

# Inventory API Gateway Module (065)

This module manages routing and configurations for inventory-related API endpoints.

## Features
- Provides full CRUD operations for Inventory API Gateway endpoints.
- Validates HTTP methods and routing paths.
- Uses standard pagination and error handling.

## Endpoints
All endpoints are available under `/api/v1/inventory-api`.

- `POST /` - Create a new endpoint configuration.
- `GET /` - List all endpoints (paginated).
- `GET /{id}` - Retrieve a specific endpoint.
- `PUT /{id}` - Update a specific endpoint.
- `DELETE /{id}` - Delete an endpoint.

## Testing
Run tests using:
```bash
pytest src/inventory/_065_inventory_api/
```

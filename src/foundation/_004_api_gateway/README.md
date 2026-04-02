# 004 API Gateway

This module provides the database models and configuration management API for the API Gateway and Rate Limiting features of Ultra ERP.

## Models
- `GatewayRoute`: Manages API paths and their target URLs.
- `RateLimitRule`: Manages rate limits (max requests per time window) for specific paths/clients.

## Features
- CRUD operations for `GatewayRoute`
- CRUD operations for `RateLimitRule`
- Comprehensive validation for URLs, paths, and limits.

## API Endpoints
All endpoints are under the prefix `/api/v1/api-gateway`.

### Routes
- `POST /routes`: Create a new route
- `GET /routes`: List all routes (paginated)
- `GET /routes/{route_id}`: Get a specific route
- `PUT /routes/{route_id}`: Update a route
- `DELETE /routes/{route_id}`: Delete a route

### Rate Limits
- `POST /rate-limits`: Create a new rate limit rule
- `GET /rate-limits`: List all rate limit rules (paginated)
- `GET /rate-limits/{rule_id}`: Get a specific rule
- `PUT /rate-limits/{rule_id}`: Update a rule
- `DELETE /rate-limits/{rule_id}`: Delete a rule

## Usage Example (Service Layer)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._004_api_gateway.schemas import GatewayRouteCreate
from src.foundation._004_api_gateway.service import create_gateway_route

async def setup_routes(db: AsyncSession):
    route_data = GatewayRouteCreate(
        path="/api/v1/users",
        target_url="http://user-service:8080/users"
    )
    route = await create_gateway_route(db, route_data)
    print(f"Created route {route.id} for {route.path}")
```

# Common Middleware Module

This module provides composable middleware for FastAPI applications in the Ultra ERP system.

## Available Middleware

- **RequestTimingMiddleware**: Measures request duration and adds `X-Response-Time` header.
- **RequestIdMiddleware**: Generates a unique request ID and adds `X-Request-ID` header.
- **CORSMiddleware**: Adds CORS support with configurable origins.
- **TenantMiddleware**: Extracts tenant ID from a configurable header.

## Usage

Register all middleware at once using `register_all_middleware`:

```python
from fastapi import FastAPI
from src.foundation._014_middleware import register_all_middleware

app = FastAPI()

# Register with default configuration from environment
register_all_middleware(app)
```

Configuration can be customized via environment variables:
- `CORS_ORIGINS`
- `CORS_ALLOW_CREDENTIALS`
- `TIMING_ENABLED`
- `REQUEST_ID_ENABLED`
- `REQUEST_ID_HEADER`
- `TENANT_HEADER_NAME`
- `TENANT_REQUIRED`

## API Endpoints

- `GET /api/v1/middleware/config`: Returns the current middleware configuration.

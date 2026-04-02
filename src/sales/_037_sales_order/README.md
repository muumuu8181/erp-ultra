# 037 Sales Order Management

This module handles Sales Orders and their items.

## Architecture

- **Models**: `SalesOrder` represents the order, and `SalesOrderItem` represents the items on the order.
- **Schemas**: Validates input data with `SalesOrderCreate`, `SalesOrderItemCreate` and outputs data via `SalesOrderResponse`.
- **Router**: Defines REST endpoints using FastAPI mapping to the `service` module functions.

## Endpoints

- `POST /api/v1/sales-orders/`: Create a new Sales Order.
- `GET /api/v1/sales-orders/{id}`: Get a Sales Order by ID.
- `GET /api/v1/sales-orders/`: List all Sales Orders with pagination.
- `PATCH /api/v1/sales-orders/{id}/status`: Update the status of a Sales Order.
- `DELETE /api/v1/sales-orders/{id}`: Delete a Sales Order.

## Example Usage

### Create a Sales Order

```http
POST /api/v1/sales-orders/
Content-Type: application/json

{
    "customer_id": 1,
    "items": [
        {
            "product_id": 10,
            "quantity": "2",
            "unit_price": "50.00"
        }
    ]
}
```

Response:
```json
{
    "id": 1,
    "code": "SO-202310-0001",
    "customer_id": 1,
    "status": "draft",
    "total_amount": "100.00",
    "items": [
        {
            "id": 1,
            "sales_order_id": 1,
            "product_id": 10,
            "quantity": "2",
            "unit_price": "50.00",
            "created_at": "...",
            "updated_at": "..."
        }
    ],
    "created_at": "...",
    "updated_at": "..."
}
```

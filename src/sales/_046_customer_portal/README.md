# Customer Portal Module (_046_customer_portal)

Provides the API layer for the customer portal, enabling customers to:
- Self-register and login
- View their dashboard (recent orders, outstanding invoices, total spend)
- View order and invoice history
- Manage their password

## Endpoints

- `POST /api/v1/portal/register`
- `POST /api/v1/portal/login`
- `GET /api/v1/portal/dashboard`
- `GET /api/v1/portal/orders`
- `GET /api/v1/portal/invoices`
- `POST /api/v1/portal/change-password`
- `POST /api/v1/portal/reset-password`

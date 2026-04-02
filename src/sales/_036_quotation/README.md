# 036 Quotation

Module for managing sales quotations.

## Features
- Create, Read, Update, Delete (via status) Quotations
- Line items calculation (subtotal, tax_amount, total_amount)
- Document transitions (Draft -> Sent -> Approved / Rejected)
- Convert Approved quotations to Sales Orders format

## Endpoints
Prefix: `/api/v1/quotations`

- `POST /` - Create a new quotation
- `GET /` - List and filter quotations
- `GET /expired` - List expired quotations
- `GET /{id}` - Get a single quotation
- `PUT /{id}` - Update a quotation (must be Draft)
- `POST /{id}/send` - Transition status to Sent
- `POST /{id}/approve` - Transition status to Approved
- `POST /{id}/reject` - Transition status to Rejected
- `POST /{id}/convert` - Get dict suitable for creating Sales Order

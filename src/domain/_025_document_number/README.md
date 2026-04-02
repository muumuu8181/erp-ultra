# 025 Document Number Generator

This module provides a unified document numbering system for the ERP.
It handles concurrent requests safely using database pessimistic locking.

## Models

- `DocumentSequence`: Stores the configuration and current sequence value for a prefix.

## Usage

```python
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.025_document_number.service import DocumentSequenceService

async def example(db: AsyncSession):
    service = DocumentSequenceService()

    # Create sequence configuration
    # Pattern allows: {prefix}, {YYYY}, {YY}, {MM}, {DD}, {seq:0Nd}
    await service.create(db, DocumentSequenceCreate(
        prefix="INV",
        pattern="{prefix}-{YYYY}{MM}-{seq:04d}",
        description="Invoice Sequence"
    ), user="system")

    # Generate the next number safely
    response = await service.generate_next_number(db, "INV")
    print(response.document_number) # e.g. "INV-202404-0001"
```

## API Endpoints

- `POST /api/v1/document-numbers`
- `GET /api/v1/document-numbers`
- `GET /api/v1/document-numbers/{id}`
- `PUT /api/v1/document-numbers/{id}`
- `DELETE /api/v1/document-numbers/{id}`
- `POST /api/v1/document-numbers/generate/{prefix}`

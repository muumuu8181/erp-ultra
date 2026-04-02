# 009_migration

Database Migration (Alembic) module. Manages schema migrations, tracks applied revisions per module, and provides an HTTP API for controlling migrations programmatically.

## Overview
This module interacts programmatically with `alembic` to provide status and controls over the database state. It stores metadata in the `migration_record` table.

## API Endpoints

- `GET /api/v1/migrations/status`: Get overall migration status
- `GET /api/v1/migrations/pending`: List pending migrations
- `POST /api/v1/migrations/apply`: Apply one or more migrations
- `POST /api/v1/migrations/rollback`: Rollback to a specific revision
- `GET /api/v1/migrations/history`: Get migration history

## Usage
Generate a migration stamp programmatically using the service:
```python
from src.foundation._009_migration.service import generate_migration_stamp

await generate_migration_stamp("_009_migration", "Create migration tables")
```

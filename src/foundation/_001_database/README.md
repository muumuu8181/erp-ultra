# 001_database

Database engine, session management, and health check.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/database/health` | DB connectivity check |

## Usage

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.foundation._001_database import get_db

@router.get("/items")
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./erp_ultra.db` | Async database URL |
| `SQL_ECHO` | `0` | Set to `1` to enable SQL logging |

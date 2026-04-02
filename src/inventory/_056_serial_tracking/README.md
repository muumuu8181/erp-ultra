# Serial Number Tracking Module

This module is responsible for tracking individual serialized products throughout their lifecycle.
It supports serial number registration, status management (in_stock, reserved, shipped, in_repair, scrapped),
full traceability via event history, and warranty tracking.

## Usage Example

```python
from fastapi import FastAPI
from src.inventory._056_serial_tracking import router as serial_router

app = FastAPI()
app.include_router(serial_router)
```

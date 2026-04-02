import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.sales._039_invoice.router import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_router_structure():
    assert router.prefix == "/api/v1/invoices"
    assert any(route.path == "/api/v1/invoices/" and "POST" in route.methods for route in router.routes)
    assert any(route.path == "/api/v1/invoices/{invoice_id}/send" and "POST" in route.methods for route in router.routes)
    assert any(route.path == "/api/v1/invoices/aging" and "GET" in route.methods for route in router.routes)

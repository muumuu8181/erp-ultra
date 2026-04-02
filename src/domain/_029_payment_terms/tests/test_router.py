"""
Tests for Payment Terms router.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

from shared.errors import NotFoundError, DuplicateError, ValidationError
from src.domain._029_payment_terms.router import router
from src.domain._029_payment_terms.schemas import PaymentTermResponse
from src.domain._029_payment_terms.models import PaymentTerm

app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Helper function to mock service returns
def mock_payment_term_response(id=1, code="NET30", name="Net 30", days=30, is_active=True):
    return PaymentTerm(
        id=id,
        code=code,
        name=name,
        description="Desc",
        days=days,
        is_active=is_active,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def mock_service():
    with patch("src.domain._029_payment_terms.router.service") as mock:
        yield mock


def test_create_payment_term_success(mock_service):
    term = mock_payment_term_response()
    mock_service.create_payment_term = AsyncMock(return_value=term)

    response = client.post(
        "/api/v1/payment-terms",
        json={"code": "NET30", "name": "Net 30", "days": 30}
    )

    assert response.status_code == 201
    assert response.json()["code"] == "NET30"


def test_create_payment_term_validation_error(mock_service):
    mock_service.create_payment_term = AsyncMock(side_effect=ValidationError("Invalid code", field="code"))

    response = client.post(
        "/api/v1/payment-terms",
        json={"code": "", "name": "Net 30", "days": 30}
    )

    assert response.status_code == 400


def test_get_payment_term_success(mock_service):
    term = mock_payment_term_response(id=1)
    mock_service.get_payment_term = AsyncMock(return_value=term)

    response = client.get("/api/v1/payment-terms/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_payment_term_not_found(mock_service):
    mock_service.get_payment_term = AsyncMock(side_effect=NotFoundError("PaymentTerm", "999"))

    response = client.get("/api/v1/payment-terms/999")

    assert response.status_code == 404


def test_list_payment_terms(mock_service):
    term1 = mock_payment_term_response(id=1, code="NET30")
    term2 = mock_payment_term_response(id=2, code="NET60")

    mock_service.list_payment_terms = AsyncMock(return_value=([term1, term2], 2))

    response = client.get("/api/v1/payment-terms")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_update_payment_term_success(mock_service):
    term = mock_payment_term_response(id=1, name="Updated")
    mock_service.update_payment_term = AsyncMock(return_value=term)

    response = client.put(
        "/api/v1/payment-terms/1",
        json={"name": "Updated"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


def test_delete_payment_term_success(mock_service):
    mock_service.delete_payment_term = AsyncMock(return_value=True)

    response = client.delete("/api/v1/payment-terms/1")

    assert response.status_code == 204

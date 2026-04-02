import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, AsyncMock
from src.domain._017_product_model.router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture
def mock_service():
    with patch('src.domain._017_product_model.router.service', new_callable=AsyncMock) as mock:
        yield mock

@patch("src.domain._017_product_model.router.get_db")
def test_create_product_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_product = AsyncMock()
    mock_product.id = 1
    mock_product.code = "PRD-00001"
    mock_product.name = "Test"
    mock_product.name_kana = None
    mock_product.description = None
    mock_product.category = None
    mock_product.sub_category = None
    mock_product.unit = "pcs"
    mock_product.standard_price = "10.0"
    mock_product.cost_price = "5.0"
    mock_product.tax_type = "standard_10"
    mock_product.weight = None
    mock_product.weight_unit = None
    mock_product.is_active = True
    mock_product.barcode = None
    mock_product.supplier_id = None
    mock_product.lead_time_days = 0
    mock_product.reorder_point = None
    mock_product.safety_stock = None
    mock_product.lot_size = None
    mock_product.memo = None
    mock_product.created_at = "2023-01-01T00:00:00Z"
    mock_product.updated_at = "2023-01-01T00:00:00Z"

    mock_service.create_product.return_value = mock_product

    data = {
        "code": "PRD-00001",
        "name": "Test",
        "unit": "pcs",
        "standard_price": 10.0,
        "cost_price": 5.0,
        "tax_type": "standard_10"
    }

    response = client.post("/api/v1/products/", json=data)
    assert response.status_code == 201
    assert response.json()["code"] == "PRD-00001"

@patch("src.domain._017_product_model.router.get_db")
def test_list_products_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_res = AsyncMock()
    mock_res.items = []
    mock_res.total = 0
    mock_res.page = 1
    mock_res.page_size = 20
    mock_res.total_pages = 0

    mock_service.list_products.return_value = mock_res

    response = client.get("/api/v1/products/")
    assert response.status_code == 200
    assert response.json()["total"] == 0

@patch("src.domain._017_product_model.router.get_db")
def test_get_product_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_product = AsyncMock()
    mock_product.id = 1
    mock_product.code = "PRD-00001"
    mock_product.name = "Test"
    mock_product.name_kana = None
    mock_product.description = None
    mock_product.category = None
    mock_product.sub_category = None
    mock_product.unit = "pcs"
    mock_product.standard_price = "10.0"
    mock_product.cost_price = "5.0"
    mock_product.tax_type = "standard_10"
    mock_product.weight = None
    mock_product.weight_unit = None
    mock_product.is_active = True
    mock_product.barcode = None
    mock_product.supplier_id = None
    mock_product.lead_time_days = 0
    mock_product.reorder_point = None
    mock_product.safety_stock = None
    mock_product.lot_size = None
    mock_product.memo = None
    mock_product.created_at = "2023-01-01T00:00:00Z"
    mock_product.updated_at = "2023-01-01T00:00:00Z"

    mock_service.get_product.return_value = mock_product

    response = client.get("/api/v1/products/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

@patch("src.domain._017_product_model.router.get_db")
def test_update_product_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_product = AsyncMock()
    mock_product.id = 1
    mock_product.code = "PRD-00001"
    mock_product.name = "Updated Name"
    mock_product.name_kana = None
    mock_product.description = None
    mock_product.category = None
    mock_product.sub_category = None
    mock_product.unit = "pcs"
    mock_product.standard_price = "10.0"
    mock_product.cost_price = "5.0"
    mock_product.tax_type = "standard_10"
    mock_product.weight = None
    mock_product.weight_unit = None
    mock_product.is_active = True
    mock_product.barcode = None
    mock_product.supplier_id = None
    mock_product.lead_time_days = 0
    mock_product.reorder_point = None
    mock_product.safety_stock = None
    mock_product.lot_size = None
    mock_product.memo = None
    mock_product.created_at = "2023-01-01T00:00:00Z"
    mock_product.updated_at = "2023-01-01T00:00:00Z"

    mock_service.update_product.return_value = mock_product

    data = {"name": "Updated Name"}

    response = client.put("/api/v1/products/1", json=data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

@patch("src.domain._017_product_model.router.get_db")
def test_deactivate_product_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_product = AsyncMock()
    mock_product.id = 1
    mock_product.code = "PRD-00001"
    mock_product.name = "Test"
    mock_product.name_kana = None
    mock_product.description = None
    mock_product.category = None
    mock_product.sub_category = None
    mock_product.unit = "pcs"
    mock_product.standard_price = "10.0"
    mock_product.cost_price = "5.0"
    mock_product.tax_type = "standard_10"
    mock_product.weight = None
    mock_product.weight_unit = None
    mock_product.is_active = False
    mock_product.barcode = None
    mock_product.supplier_id = None
    mock_product.lead_time_days = 0
    mock_product.reorder_point = None
    mock_product.safety_stock = None
    mock_product.lot_size = None
    mock_product.memo = None
    mock_product.created_at = "2023-01-01T00:00:00Z"
    mock_product.updated_at = "2023-01-01T00:00:00Z"

    mock_service.deactivate_product.return_value = mock_product

    response = client.delete("/api/v1/products/1")
    assert response.status_code == 200
    assert response.json()["is_active"] is False

@patch("src.domain._017_product_model.router.get_db")
def test_create_category_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_cat = AsyncMock()
    mock_cat.id = 1
    mock_cat.name = "Tech"
    mock_cat.parent_id = None
    mock_cat.sort_order = 0
    mock_cat.is_active = True
    mock_cat.created_at = "2023-01-01T00:00:00Z"
    mock_cat.updated_at = "2023-01-01T00:00:00Z"

    mock_service.create_category.return_value = mock_cat

    data = {"name": "Tech"}

    response = client.post("/api/v1/products/categories", json=data)
    assert response.status_code == 201
    assert response.json()["name"] == "Tech"

@patch("src.domain._017_product_model.router.get_db")
def test_list_categories_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_service.list_categories.return_value = []

    response = client.get("/api/v1/products/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@patch("src.domain._017_product_model.router.get_db")
def test_search_products_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_res = AsyncMock()
    mock_res.items = []
    mock_res.total = 0
    mock_res.page = 1
    mock_res.page_size = 20
    mock_res.total_pages = 0

    mock_service.search_products.return_value = mock_res

    response = client.get("/api/v1/products/search?q=test")
    assert response.status_code == 200
    assert response.json()["total"] == 0

@patch("src.domain._017_product_model.router.get_db")
def test_update_product_pricing_route(mock_get_db, mock_service):
    mock_db = AsyncMock()
    mock_get_db.return_value = mock_db

    mock_product = AsyncMock()
    mock_product.id = 1
    mock_product.code = "PRD-00001"
    mock_product.name = "Test"
    mock_product.name_kana = None
    mock_product.description = None
    mock_product.category = None
    mock_product.sub_category = None
    mock_product.unit = "pcs"
    mock_product.standard_price = "15.0"
    mock_product.cost_price = "5.0"
    mock_product.tax_type = "standard_10"
    mock_product.weight = None
    mock_product.weight_unit = None
    mock_product.is_active = True
    mock_product.barcode = None
    mock_product.supplier_id = None
    mock_product.lead_time_days = 0
    mock_product.reorder_point = None
    mock_product.safety_stock = None
    mock_product.lot_size = None
    mock_product.memo = None
    mock_product.created_at = "2023-01-01T00:00:00Z"
    mock_product.updated_at = "2023-01-01T00:00:00Z"

    mock_service.update_pricing.return_value = mock_product

    data = {"standard_price": 15.0}

    response = client.put("/api/v1/products/1/pricing", json=data)
    assert response.status_code == 200
    assert response.json()["standard_price"] == "15.0"
